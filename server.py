import argparse
import socket
import os
import selectors
import argparse

sel = selectors.DefaultSelector()
sockets = []
users = []

def accept(sock,mask):
    conn, address = sock.accept()
    sockets.append(conn)
    print("Accepted connection from client Address: ", address )
    sockets.append(conn)
    conn.setblocking(False)
    data = conn.recv(1024)  
    if data:
        data=data.decode()
        users.append(data)
        print(users)
        print("Connection to client established, waiting to recive messages from user: ",data)
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(1024)  
    if data:
        print(data.decode())
        #conn.sendall(data) 
        broadcast(conn,data.decode()) 
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

def broadcast(conn, message):
    message = message.encode()
    for socket in sockets:
        if socket != conn:
            socket.send(message)


def main():

    serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_socket.bind(('',0))
    server_port = serv_socket.getsockname()[1]
    print("will wait for client connection at port " , server_port)
    serv_socket.listen(100)
    serv_socket.setblocking(False)
    print("Waiting for incoming client connection ...")
    sel.register(serv_socket, selectors.EVENT_READ,)


    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            #callback = key.data
            #callback(key.fileobj, mask)
            if key.data is None:
               accept(key.fileobj,mask)
            else:
               read(key.fileobj, mask)


if __name__ == '__main__':
    main()
