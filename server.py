import socket
import os
import signal
import sys
import selectors

# Selector for helping us select incoming data and connections from multiple sources.

sel = selectors.DefaultSelector()

# Client list for mapping connected clients to their connections.

client_list = []

# Dictionary of follow_lists

dict_of_follow_lists = {}

# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message='DISCONNECT CHAT/1.0\n'
    for reg in client_list:
        reg[1].send(message.encode())
    sys.exit(0)

# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

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

# Search the client list for a particular user.

def client_search(user):
    for reg in client_list:
        if reg[0] == user:
            return reg[1]
    return None

# Search the client list for a particular user by their socket.

def client_search_by_socket(sock):
    for reg in client_list:
        if reg[1] == sock:
            return reg[0]
    return None

# Add a user to the client list.

def client_add(user, conn):
    registration = (user, conn)
    client_list.append(registration)
    temp = "@all"
    temp2 = "@"+user
    client_follow_list = [temp, temp2]
    dict_of_follow_lists[user] = client_follow_list

# Remove a client when disconnected.

def client_remove(user):
    for reg in client_list:
        if reg[0] == user:
            client_list.remove(reg)
            break

# Loop through list of registered clients and return the list as a string.

def get_client_list():
    client_list_string = ""
    for reg in client_list:
        client_list_string += reg[0] + ", "
    return client_list_string

# Add value to dict_of_follow_lists

def add_values_in_dict(key, list_of_values):
    if key not in dict_of_follow_lists:
        dict_of_follow_lists[key] = list()
    dict_of_follow_lists[key].extend(list_of_values)

# Search for value in dict_of_follow_lists, return list of keys with that value

def get_keys_with_value(value):
    list_of_keys = [key
                for key, list_of_values in dict_of_follow_lists.items()
                if value in list_of_values]
    return list_of_keys

# Function to read messages from clients.

def read_message(sock, mask):
    message = get_line_from_socket(sock)

    # Does this indicate a closed connection?

    if message == '':
        print('Closing connection')
        sel.unregister(sock)
        sock.close()

    # Receive the message.  

    else:
        user = client_search_by_socket(sock)
        print(f'Received message from user {user}:  ' + message)
        words = message.split(' ')

        # Check for client disconnections.  
 
        if words[0] == 'DISCONNECT':
            print('Disconnecting user ' + user)
            client_remove(user)
            sel.unregister(sock)
            sock.close()
        
        # Remove the ":" from the end of the user name. 
        words[0] = words[0][:-1]

        # If !list is recieved, send the list of registered clients as a comma-separated string.
        if words[1] == "!list":
            returned_list = get_client_list()
            forwarded_message = f'{returned_list}\n'
            sock.send(forwarded_message.encode())
        # If "!follow?" is recieved, send the list of followed items as a comma-separated string.
        elif words[1] == '!follow?':
            message = dict_of_follow_lists[user].encode()
            client_search(user).send(message)
        # If "!follow" is recieved, add the term that follows to the list of followed users.
        elif words[1] == '!follow' and words[2] == 'term':
            dict_of_follow_lists[user].append(words[3])
            for x in range(len(dict_of_follow_lists)):
               print(dict_of_follow_lists[x])

        # Send message to all users.  Send at most only once, and don't send to yourself. 
        # Need to re-add stripped newlines here.

        else:
            for reg in client_list:
                if reg[0] == user:
                    continue
                client_sock = reg[1]
                forwarded_message = f'{message}\n'
                client_sock.send(forwarded_message.encode())

# Function to accept and set up clients.

def accept_client(sock, mask):
    conn, addr = sock.accept()
    print('Accepted connection from client address:', addr)
    message = get_line_from_socket(conn)
    message_parts = message.split()

    # Check format of request.

    if ((len(message_parts) != 3) or (message_parts[0] != 'REGISTER') or (message_parts[2] != 'CHAT/1.0')):
        print('Error:  Invalid registration message.')
        print('Received: ' + message)
        print('Connection closing ...')
        response='400 Invalid registration\n'
        conn.send(response.encode())
        conn.close()

    # If request is properly formatted and user not already listed, go ahead with registration.

    else:
        user = message_parts[1]

        if (client_search(user) == None):
            client_add(user,conn)
            print(f'Connection to client established, waiting to receive messages from user \'{user}\'...')
            response='200 Registration succesful\n'
            conn.send(response.encode())
            conn.setblocking(False)
            sel.register(conn, selectors.EVENT_READ, read_message)

        # If user already in list, return a registration error.

        else:
            print('Error:  Client already registered.')
            print('Connection closing ...')
            response='401 Client already registered\n'
            conn.send(response.encode())
            conn.close()


# Our main function.

def main():

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(100)
    server_socket.setblocking(False)
    sel.register(server_socket, selectors.EVENT_READ, accept_client)
    print('Waiting for incoming client connections ...')
     
    # Keep the server running forever, waiting for connections or messages.
    
    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)    

if __name__ == '__main__':
    main()

