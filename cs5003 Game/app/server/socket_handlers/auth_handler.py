"""Authentication-related socket event handlers"""

from flask_socketio import join_room
from flask import request
from app.shared.protocols import SOCKET_EVENTS
from .base_handler import BaseSocketHandler

class AuthSocketHandler(BaseSocketHandler):
    def __init__(self, socketio):
        super().__init__(socketio)
        self.user_sessions = {}
    
    def register_handlers(self):
        """register auth-related socket handlers"""
        @self.socketio.on(SOCKET_EVENTS["CONNECT"])
        def on_connect():
            print("Client connected")
        
        @self.socketio.on('authenticate')
        def on_authenticate(data):
            """User authentication, save username to sid mapping"""
            if 'username' in data:
                username = data['username']
                self.user_sessions[username] = request.sid
                print(f"User {username} authenticated with sid {request.sid}")
                
                # Join personal room
                join_room(username)
                
        @self.socketio.on('disconnect')
        def on_disconnect():
            """Handle user disconnection, clean up mapping"""
            sid = request.sid
            # Find and remove user from mapping
            for username, session_id in list(self.user_sessions.items()):
                if session_id == sid:
                    del self.user_sessions[username]
                    print(f"User {username} disconnected")
    
    def get_user_sessions(self):
        """Return the user sessions mapping"""
        return self.user_sessions