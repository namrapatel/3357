## Installation
1. Use `cd` to move into the directory containing these files
2. Use  `pip install` to download dependencies
3. Start the server using `python server.py`
        - This will return a 5 digit port number for use in the next step
4. Start a client using `python client.py chat://localhost:{PORT} {username}` where PORT is the port number from step 3, and username is the username you desire to use in this chatroom
5. You now have a client connected to the server, repeat step (4) for up to 100 clients
