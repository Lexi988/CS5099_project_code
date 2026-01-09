"""Game-related socket event handlers"""

from flask_socketio import emit, join_room, leave_room
from app.shared.protocols import SOCKET_EVENTS
from app.server.game_logic import GameManager
from .base_handler import BaseSocketHandler

class GameSocketHandler(BaseSocketHandler):
    def __init__(self, socketio, game_manager=None):
        super().__init__(socketio)
        self.game_manager = game_manager or GameManager()
    
    def register_handlers(self):
        """Register game-related socket handlers"""
        @self.socketio.on(SOCKET_EVENTS["CREATE_GAME"])
        def on_create_game(data):
            """Handle game creation"""
            game_id = self.game_manager.create_new_game(data)
            emit(SOCKET_EVENTS["GAME_CREATED"], {"game_id": game_id})
    
        @self.socketio.on(SOCKET_EVENTS["JOIN_GAME"])
        def on_join_game(data):
            """Handle player joining a game"""
            game_id = data["game_id"]
            username = data["username"]
            join_room(game_id)
            self.game_manager.add_player(game_id, username)
            emit(SOCKET_EVENTS["PLAYER_JOINED"], {"username": username}, room=game_id)
    
        @self.socketio.on(SOCKET_EVENTS["MAKE_MOVE"])
        def on_move(data):
            """Handle player moves and broadcast updates"""
            emit(SOCKET_EVENTS["GAME_UPDATE"], data, room=data["game_id"])
    
        @self.socketio.on(SOCKET_EVENTS["LEAVE_GAME"])
        def on_leave(data):
            """Handle player leaving a game"""
            leave_room(data["game_id"])