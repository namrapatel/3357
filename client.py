import socket
import sys
import select
import argparse
from urllib.parse import urlparse
import signal

# Constants to store string messages that will be recieved from server
REGISTRATION_ERROR = "400 Invalid registration"
CLIENT_REGISTERED_ERROR = "401 Client already registered"
REGISTRATION_SUCCESSFUL = "200 Registration successful"
DISCONNECT_MESSAGE = "Disconnected from server, exiting..."

def main(path, username):

    url = urlparse(path) # Store path argument in url
    serverPort = url.port # Store port from the url in serverPort
    serverHost = url.hostname # Store host from the url in serverHost
    print('Connecting to server...')
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Initialize clientSocket
    clientSocket.connect((serverHost, serverPort)) # Connect clientSocket to the HOST and PORT specificed in terminal arguments
    clientSocket.setblocking(False) # Make clientSocket non-blocking
    clientSocket.send(("REGISTER " + username + " CHAT/1.0").encode()) # Send encoded registration message to server

    # Asyncronously watch for "CTRL + c" commands from user, if recieved, send disconnection notice to server, close clientSocket, exit program
    def handler(signum, frame):
        print("Interrupt recieved, shutting down...")
        disconnectMessage = "DISCONNECT " + username + " CHAT/1.0"
        clientSocket.send(disconnectMessage.encode())
        clientSocket.close()
        sys.exit()
    
    signal.signal(signal.SIGINT, handler) # Look for SIGINT signal ("CTRL + c")

    while True:
        try:
            while True:
                socketsList = [sys.stdin, clientSocket] # Maintain a list of sockets
                clientSocket.setblocking(False) 
                readSockets, writeSockets, errorSockets = select.select(socketsList,[],[]) # Use .select to constantly find list of read-ready sockets

                # Loop through readSockets (read-ready sockets)
                for socks in readSockets:

                    if socks == clientSocket: # If clientSocket is ready-ready, then do the following
                        message = socks.recv(2048) # Listen to socket and store incoming messages in message
                        
                        # If incoming message is CLIENT_REGISTERED_ERROR, print error and throw Exception
                        if (message.decode().find(CLIENT_REGISTERED_ERROR) != -1):
                            print("401 Client already registered")
                            raise Exception

                        # If incoming message is DISCONNECT_MESSAGE, print decoded message, close clientSocket, and exit program
                        if (message.decode().find(DISCONNECT_MESSAGE) != -1):
                            print(message.decode())
                            clientSocket.close()
                            sys.exit()

                        # If incoming message is REGISTRATION_SUCCESSFUL, print success strings and break loop
                        if (message.decode().find(REGISTRATION_SUCCESSFUL) != -1):
                            print("Connection to server established. Sending intro message... \n")
                            print("Registration successful. Ready for Messaging!")
                            break
                    
                        print(message.decode()) # Convert message from bytes to str and print
                        
                    else: #clientSocket was not read-ready, so we look for input from user
                        message = sys.stdin.readline() # Take input from user and store in message
                        message = "@" + username + ": " + message # Concatenate "@username: " to message
                        clientSocket.send(message.encode()) # Convert message from str to bytes and send
                        print("\n")

        # Exception handling
        except BlockingIOError as e:
            pass
        except Exception as e:
            print(e)
            sys.exit()
    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Client')
    parser.add_argument('path', type = str) # First argument from terminal is the path
    parser.add_argument('username', type = str) # Second argument from terminal is the username
    arguments = parser.parse_args()
    main(arguments.path, arguments.username) # Call main method with path and username as params
