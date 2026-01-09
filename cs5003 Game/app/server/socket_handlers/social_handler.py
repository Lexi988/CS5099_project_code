"""Social feature socket event handlers"""

import time
from flask_socketio import emit
from app.shared.protocols import SOCKET_EVENTS
from .base_handler import BaseSocketHandler

class SocialSocketHandler(BaseSocketHandler):
    def __init__(self, socketio):
        super().__init__(socketio)
    
    def register_handlers(self):
        """Register social feature socket handlers"""
        @self.socketio.on(SOCKET_EVENTS["SEND_MESSAGE"])
        def on_send_message(data):
            """Handle message sending events and notify recipient"""
            sender = data["sender"]
            receiver = data["receiver"]
            content = data["content"]
            
            # Send to receiver's room
            emit(
                SOCKET_EVENTS["NEW_MESSAGE"], 
                {"sender": sender, "content": content, "timestamp": int(time.time())},
                room=receiver
            )
            
        @self.socketio.on('friend_request')
        def on_friend_request(data):
            """Handle friend request events and notify recipient"""
            from_user = data["from_user"]
            to_user = data["to_user"]
            
            # Send to receiver's room
            emit(
                SOCKET_EVENTS["FRIEND_REQUEST"],
                {"from_user": from_user},
                room=to_user
            )