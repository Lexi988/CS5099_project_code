"""Socket.IO manager that coordinates all socket handlers"""

from app.server.socket_handlers.auth_handler import AuthSocketHandler
from app.server.socket_handlers.game_handler import GameSocketHandler
from app.server.socket_handlers.social_handler import SocialSocketHandler
from app.server.game_logic import GameManager

class SocketManager:
    """Manager for Socket.IO functionality"""
    
    def __init__(self, socketio):
        """Init. the Socket.IO manager"""
        #create shared game manager
        self.game_manager = GameManager()

        self.game_manager.bind(socketio)
        
        # Init. handlers
        self.auth_handler = AuthSocketHandler(socketio)
        self.game_handler = GameSocketHandler(socketio, self.game_manager)
        self.social_handler = SocialSocketHandler(socketio)
        
        #reg. all handlers
        self.auth_handler.register_handlers()
        self.game_handler.register_handlers()
        self.social_handler.register_handlers()
        
    def get_user_sessions(self):
        """Get user to session ID mapping"""
        return self.auth_handler.get_user_sessions()