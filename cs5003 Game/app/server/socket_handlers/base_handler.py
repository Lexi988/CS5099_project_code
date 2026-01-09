"""Base class for socket event handlers"""

class BaseSocketHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        
    def register_handlers(self):
        """Register all handlers defined in this class"""
        raise NotImplementedError("Subclasses must implement this method")