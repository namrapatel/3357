import socket
import sys
import selectors

sel = selectors.DefaultSelector()
sockets = {}
serv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def accept(sock,mask):
    conn, address = sock.accept()
    conn.setblocking(False)
    username = conn.recv(1024)  
    username = username.decode()
    username = username.strip("REGISTER " + " CHAT/1.0")
    # check if username exists in userList
    if (any(username in sublist for sublist in sockets.items())):
        sendToSelected(conn, "401 Client already registered")
        sel.register(conn, selectors.EVENT_READ, read)
        print("Client already registered, rejecting...")
        return

    sockets[conn] = username
    print("Accepted connection from client address: ", address)
    print("Connection to client established, waiting to recive messages from user: ", username)
    sendToSelected(conn, "200 Registration successful")
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    message = conn.recv(1024)  
    message = message.decode()
    if message:
        if (message.find("DISCONNECT") != -1):
            handleClientDisconnect(conn, message)
        else:
            if (message.find("REGISTER") == -1):
                print(message)
                broadcast(conn, message) 
            
        
def broadcast(conn, message):
    message = message.encode()
    for key in sockets:
        if key != conn:
            key.send(message)

def sendToSelected(conn, message):
    message = message.encode()
    for key in sockets:
        if key == conn:
            key.send(message)

def handleClientDisconnect(conn, message):
    for connection, username in sockets.items():
        if (message.find(username) != -1):
            print("Disconnecting user ", username)
            sockets.pop(getKey(sockets, username))
            sel.unregister(conn)
            conn.close()
            break
    if (len(sockets) <= 1):
        for key in sockets:
            remainingSocket = key
        remainingSocket.send("Disconnected from server, exiting...".encode())
        remainingSocket.close()
        serv_socket.close()
        sys.exit()

def getKey(dict, val):
    for key, value in dict.items():
        if val == value:
             return key
 
    return "Key not found"

def main():
    serv_socket.bind(('',0))
    server_port = serv_socket.getsockname()[1]
    print("will wait for client connection at port " , server_port)
    serv_socket.listen(100)
    serv_socket.setblocking(False)
    print("Waiting for incoming client connection ...")
    sel.register(serv_socket, selectors.EVENT_READ,)

    while True:
        try: 
            events = sel.select(timeout=None)
            for key, mask in events:
                #callback = key.data
                #callback(key.fileobj, mask)
                if key.data is None:
                    accept(key.fileobj,mask)
                else:
                    read(key.fileobj, mask)
        except BlockingIOError as e:
            pass
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()