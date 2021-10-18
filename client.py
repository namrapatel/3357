import socket
from sys import argv
import selectors
import argparse
from urllib.parse import urlparse

sel = selectors.DefaultSelector()

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
    while True:
        try:
            while True:
                sentence = input()
                clientSocket.setblocking(False)
                clientSocket.send(sentence.encode())
                print("sent")
                modifiedSentence = clientSocket.recv(1024)
                print("From Server: ", modifiedSentence.decode())
                #if(sentence=='quit'): break;

        except BlockingIOError as e:
            pass

        except Exception as e:
            # Other exceptiopns are handled here
            print('Reading error: '.format(str(e)))
            sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('path',type=str)
    parser.add_argument('username',type=str)
    arguments= parser.parse_args()
    main(arguments.path, arguments.username)
