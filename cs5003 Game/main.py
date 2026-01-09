#/main.py
#!/usr/bin/env python3

#import libs:
import sys
import tkinter as tk
from app.controller.client_controller import launch_application
from app.server.socket_controller import register_sockets

"""
Entry point for the Crossword application.  
This script will:

CLA: 'server' -> start the Flask + Socket.io server  -> launch the Tkinter client GUI  
    python main.py server   #start server on port 5001
    python main.py          #launch client app.

"""
def run_server():
    """
    config + run server
    """
    from flask import Flask
    from flask_socketio import SocketIO
    from app.controller.server_controller import register_routes
    from app.server.socket_controller import register_sockets
    from app.server.game_manager import GameManager

    app = Flask(__name__)
    app.config.from_object('app.config')
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    #create game manager and reg. sockets
    register_routes(app)
    socket_manager = register_sockets(socketio)  #handles game_manager creation + binding
    
    socketio.run(app,
             host='0.0.0.0',
             port=5001,
             debug=True,)

def run_client():
    #config. and run the client gui

    root = tk.Tk()
    root.title("Crossword Client")
    launch_application(root)
    root.mainloop()

if __name__ == "__main__":
    #first CLI arg = 'server' start server; else = launch client GUI
    if len(sys.argv)>1 and sys.argv[1].lower()=="server":
        run_server()
    else:
        run_client()
#entry point for both server and client