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
    sel.register(clientSocket,selectors.EVENT_READ | selectors.EVENT_WRITE,)


    print("Registration successful. Ready for Messaging!")
    while True:
        sentence = input()
        events = sel.select(timeout=None)
        for key, mask in events:
            if mask & selectors.EVENT_READ:
                modifiedSentence = clientSocket.recv(1024)
                print("From Server: ", modifiedSentence.decode())
            if mask & selectors.EVENT_WRITE:
                if not sentence:
                    sel.modify(clientSocket,selectors.EVENT_READ)
                else:
                    clientSocket.send(sentence.encode())
        #modifiedSentence = clientSocket.recv(1024)
        #print("From Server: ", modifiedSentence.decode())
        if(sentence=='quit'): break;
    clientSocket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('path',type=str)
    parser.add_argument('username',type=str)
    arguments= parser.parse_args()
    main(arguments.path, arguments.username)
