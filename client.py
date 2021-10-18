import socket
import sys
import selectors
import argparse
from urllib.parse import urlparse

sel = selectors.DefaultSelector()
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
    while True:
        try:
            while True:
                clientSocket.setblocking(False)
                sentence = sys.stdin.readline()
                clientSocket.send(sentence.encode())
                modifiedSentence = clientSocket.recv(1024)
                print("From Server: ", modifiedSentence.decode())
                if (modifiedSentence.decode().find(registeredError) != -1):
                    raise Exception
                print("sent")

        except BlockingIOError as e:
            # print(e)
            pass

        except Exception as e:
            print(e)
            if (e==0):
                print("401 Client already registered")
            sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('path',type=str)
    parser.add_argument('username',type=str)
    arguments= parser.parse_args()
    main(arguments.path, arguments.username)
