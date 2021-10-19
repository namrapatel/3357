import socket
import sys
import selectors

selector = selectors.DefaultSelector() # Initialize selector
registry = {} # Create a dictionary to hold sockets and usernames as key-value pairs
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Initialize the main socket for the server

# Accept and handle new socket connections to serverSocket
def accept(sock,mask):

    connectionSocket, address = sock.accept() # Accept connection and store connection socket and address
    connectionSocket.setblocking(False) # Make new socket non-blocking
    
    # Listen to connectionSocket and accept maximum 1024 bytes, store 
    # in username, then turn username from bytes to str
    username = connectionSocket.recv(1024).decode() 
    username = username.strip("REGISTER " + " CHAT/1.0") # Remove registration message chars from username 
    
    # Check if username exists in the registry, if so, send error message and move selector back to READ-mode
    if (any(username in sublist for sublist in registry.items())):
        sendToSelected(connectionSocket, "401 Client already registered")
        selector.register(connectionSocket, selectors.EVENT_READ, read)
        print("Client already registered, rejecting...")
        return

    registry[connectionSocket] = username # Store connectionSocket and username in registry dictionary
    print("Accepted connection from client address: ", address)
    print("Connection to client established, waiting to recive messages from user: ", username)
    sendToSelected(connectionSocket, "200 Registration successful") # Send successful registration message to new connectionSocket
    selector.register(connectionSocket, selectors.EVENT_READ, read) # Put selector back in READ-mode for future use

# Read and handle messages from existing connectionSockets
def read(connectionSocket, mask):

     # Listen to connectionSocket, convert incoming message from bytes to str and store in message
    message = connectionSocket.recv(1024).decode()

    if message:
        # Check if recieved message is a disconnection message, if so, handle, else, print message to server 
        # console and broadcast it to all connectionSockets (clients) except sender
        if (message.find("DISCONNECT") != -1): 
            handleClientDisconnect(connectionSocket, message)
        else: 
            print(message) 
            broadcast(connectionSocket, message) 
            
# Broadcast message to all connectionSockets (clients) except the connectionSocket passed in params
def broadcast(connectionSocket, message):

    message = message.encode() # Convert message from str to bytes 

    for key in registry:
        if key != connectionSocket:
            key.send(message)

# Send message to the connectionSocket (client) specificed in params from registry 
def sendToSelected(connectionSocket, message):

    message = message.encode() # Convert message from str to bytes 

    for key in registry:
        if key == connectionSocket:
            key.send(message)

# Helper method to handle disconnecting clients, passed connectionSocket (client who sent message), and disconnection message (message)
def handleClientDisconnect(connectionSocket, message):

    checkRegistry() # Check registry to see if this was the only client

    # Check if any usernames from the registry can be found in the disconnection message, if so, remove the client with that username
    for connection, username in registry.items():
        if (message.find(username) != -1): 
            print("Disconnecting user ", username)
            registry.pop(getKey(registry, username))
            selector.unregister(connectionSocket) # Unregister this client from selector
            connectionSocket.close() # Close this client's socket
            break
    
    checkRegistry() # Check registry to see how many clients remain post-removal
    
# Helper method that checks if registry has 1 or less user remaining, is so, shuts down the server
def checkRegistry():

    if (len(registry) <= 1):
        for key in registry:
            remainingSocket = key # Get remaining client's socket
        remainingSocket.send("Disconnected from server, exiting...".encode()) # Send last remaining client a disconnection notice
        remainingSocket.close() # Close remaining client's socket
        serverSocket.close() # Close main server socket
        sys.exit() # Exit program

# Given a dictionary and a value, return the key for that respective value, else return "Key not found"
def getKey(dict, val):
    for key, value in dict.items():
        if val == value:
             return key
 
    return "Key not found"

def main():
    serverSocket.bind(('',0)) # Bind server's socket with any available HOST and PORT, respectively
    serverPort = serverSocket.getsockname()[1] # Store PORT number
    print("Will wait for client connection at port " , serverPort)
    serverSocket.listen(100) # Open server socket to 100 connections
    serverSocket.setblocking(False) # Make the server socket non-blocking
    print("Waiting for incoming client connection ...")
    selector.register(serverSocket, selectors.EVENT_READ,) # Register selector in READ-mode to listen for events

    while True:
        try: 
            # Use selector's READ/WRITE event handling to intelligently accept new connections or read from existing connections
            events = selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept(key.fileobj, mask) # This method accepts and handles new connections to serverSocket
                else:
                    read(key.fileobj, mask) # This method reads messages sent to serverSocket from existing socket connections
        
        # Exception handling
        except BlockingIOError as e:
            pass
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()