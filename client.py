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
   
    url = urlparse(path)
    serverPort = url.port
    serverHost = url.hostname
    print('Connecting to server...')
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((serverHost,serverPort))
    clientSocket.setblocking(False)
    clientSocket.send(("REGISTER " + username + " CHAT/1.0").encode())

    def handler(signum, frame):
        print("Interrupt recieved, shutting down...")
        disconnectMessage = "DISCONNECT " + username + " CHAT/1.0"
        clientSocket.send(disconnectMessage.encode())
        clientSocket.close()
        sys.exit()
    
    signal.signal(signal.SIGINT, handler)

    while True:
        try:
            while True:
                sockets_list = [sys.stdin, clientSocket]
                clientSocket.setblocking(False)
                read_sockets, write_socket, error_socket = select.select(sockets_list,[],[])
                for socks in read_sockets:
                    if socks == clientSocket:
                        message = socks.recv(2048)
                        if (message.decode().find(CLIENT_REGISTERED_ERROR) != -1):
                            print("401 Client already registered")
                            raise Exception
                        if (message.decode().find(DISCONNECT_MESSAGE) != -1):
                            print(message.decode())
                            clientSocket.close()
                            sys.exit()
                        if (message.decode().find(REGISTRATION_SUCCESSFUL) != -1):
                            print("Connection to server established. Sending intro message... \n")
                            print("Registration successful. Ready for Messaging!")
                            break
                        print(message.decode())
                        
                    else:
                        message = sys.stdin.readline()
                        message = "@" + username + ": " + message
                        clientSocket.send(message.encode())
                        print("\n")

        except BlockingIOError as e:
            # print(e)
            pass

        except Exception as e:
            print(e)
            sys.exit()
    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('path', type = str)
    parser.add_argument('username', type = str)
    arguments= parser.parse_args()
    main(arguments.path, arguments.username)
