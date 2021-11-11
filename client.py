import socket
import os
import signal
import sys
import argparse
from urllib.parse import urlparse
import selectors

# Selector for helping us select incoming data from the server and messages typed in by the user.

sel = selectors.DefaultSelector()

# Socket for sending messages.

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# User name for tagging sent messages.

user = ''

# Signal handler for graceful exiting.  Let the server know when we're gone.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message=f'DISCONNECT {user} CHAT/1.0\n'
    client_socket.send(message.encode())
    sys.exit(0)

# Simple function for setting up a prompt for the user.

def do_prompt(skip_line=False):
    if (skip_line):
        print("")
    print("> ", end='', flush=True)

# Read a single line (ending with \n) from a socket and return it.
# We will strip out any \r and \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Collect information about file, setup a new file that will store the incoming packets from the server
def recieve_file(words, sock):
    # Ensure that recieved info has a length of 6
    if len(words) == 6:
        # Collect file information from the message recieved from the server
        file_sender = words[1]
        file_name = words[2]
        file_size = words[3]
        buffer_size = words[4]
        buffer_size = int(buffer_size)
        number_of_packets = words[5]
        number_of_packets = int(number_of_packets)

        # Print header information as specificed by assignment document
        print(f'\nIncoming file: {file_name}')
        print(f'Origin: {file_sender}')
        print(f'Content-Length: {file_size}')

        # Create a new file to store the recieved packets
        file = open(file_name, 'w')
        for i in range(0, number_of_packets):
            recieved_packet = sock.recv(buffer_size).decode()
            file.write(recieved_packet)
        print('\nFile recieved, check current directory to view it.')

    else:
        print('Error: Invalid message from server, file not recieved.')
        return


# Read file from local storage, send server information about file size to prepare, send file in chunks to server
def send_file(words, sock):
    buffer_size = 4096 # 4KB
    file_name = words[1]

    file = open(file_name, 'r')
    data=file.read() 
    
    # Get file size and find number of packets needed to send
    file_size = len(data) 
    number_of_packets = int(file_size//buffer_size)
    if file_size % buffer_size > 0:
        number_of_packets += 1

    # Send the file metadata to the server so it knows how to setup to recieve the file
    file_info = f'{file_size}, {buffer_size}, {number_of_packets}\n'
    file_info = file_info.encode()
    client_socket.send(file_info)

    # Try sending the file to the server in chunks, if it fails, print an error to the client
    try:
        while data != '':
            sent_packet = data[:buffer_size]    # queue up the next amount of bytes to be sent
            sent_packet = sent_packet.encode()
            client_socket.send(sent_packet)
            data = data[buffer_size:] # begin to deplete the size of the file to keep track of what's been sent
            print("File was sent to the server.")
            do_prompt()
    except Exception as e:    
        print(e)
        print("Error: File was not sent to the server.")
        

# Function to handle incoming messages from server.  Also look for disconnect messages to shutdown.

def handle_message_from_server(sock, mask):
    message=get_line_from_socket(sock)
    words=message.split(' ')
    print()
    if words[0] == 'DISCONNECT':
        print('Disconnected from server ... exiting!')
        sys.exit(0)
    elif words[0] == 'RECEIVE':
        recieve_file(words, sock)
    elif words[0] == 'SEND':
        send_file(words, sock)
    else:
        print(message)
        do_prompt()

# Function to handle incoming messages from user.

def handle_keyboard_input(file, mask):
    line=sys.stdin.readline()
    message = f'@{user}: {line}'
    client_socket.send(message.encode())
    do_prompt()

# Our main function.

def main():

    global user
    global client_socket

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments to retrieve a URL.

    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="user name for this user on the chat service")
    parser.add_argument("server", help="URL indicating server location in form of chat://host:port")
    args = parser.parse_args()

    # Check the URL passed in and make sure it's valid.  If so, keep track of
    # things for later.

    try:
        server_address = urlparse(args.server)
        if ((server_address.scheme != 'chat') or (server_address.port == None) or (server_address.hostname == None)):
            raise ValueError
        host = server_address.hostname
        port = server_address.port
    except ValueError:
        print('Error:  Invalid server.  Enter a URL of the form:  chat://host:port')
        sys.exit(1)
    user = args.user

    # Now we try to make a connection to the server.

    print('Connecting to server ...')
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        sys.exit(1)

    # The connection was successful, so we can prep and send a registration message.
    
    print('Connection to server established. Sending intro message...\n')
    message = f'REGISTER {user} CHAT/1.0\n'
    client_socket.send(message.encode())
   
    # Receive the response from the server and start taking a look at it

    response_line = get_line_from_socket(client_socket)
    response_list = response_line.split(' ')
        
    # If an error is returned from the server, we dump everything sent and
    # exit right away.  
    
    if response_list[0] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        print(response_line)
        print('Exiting now ...')
        sys.exit(1)   
    else:
        print('Registration successful.  Ready for messaging!')

    # Set up our selector.

    client_socket.setblocking(False)
    sel.register(client_socket, selectors.EVENT_READ, handle_message_from_server)
    sel.register(sys.stdin, selectors.EVENT_READ, handle_keyboard_input)
    
    # Prompt the user before beginning.

    do_prompt()

    # Now do the selection.

    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)    



if __name__ == '__main__':
    main()
