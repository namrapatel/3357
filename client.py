import socket
import sys
import select
import argparse
from urllib.parse import urlparse
import signal

registeredError = "401 Client already registered"

def main(path, username):
   
    url = urlparse(path)
    serverPort = url.port
    serverName = url.hostname
    print('Connecting to server...')
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((serverName,serverPort))
    clientSocket.setblocking(False)
    print('Connection to server established. Sending intro message...')
    clientSocket.send(username.encode())

    print("Registration successful. Ready for Messaging!")

    def handler(signum, frame):
        res = input("Interrupt recieved, shutting down...")
        disconnectMessage = "DISCONNECT " + username + " CHAT/1.0"
        clientSocket.send(disconnectMessage.encode())
        exit()
    
    signal.signal(signal.SIGINT, handler)

    while True:
        try:
            while True:
                sockets_list = [sys.stdin, clientSocket]
                clientSocket.setblocking(False)
                read_sockets,write_socket, error_socket = select.select(sockets_list,[],[])
 
                for socks in read_sockets:
                    if socks == clientSocket:
                        message = socks.recv(2048)
                        if (message.decode().find(registeredError) != -1):
                            print("401 Client already registered")
                            raise Exception
                        print(message.decode())
                        
                    else:
                        message = sys.stdin.readline()
                        message = "@" + username + ": " + message
                        clientSocket.send(message.encode())
                        print("<You>" + message)
                

        except BlockingIOError as e:
            # print(e)
            pass

        except Exception as e:
            print(e)
            sys.exit()
    
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('path',type=str)
    parser.add_argument('username',type=str)
    arguments= parser.parse_args()
    main(arguments.path, arguments.username)
