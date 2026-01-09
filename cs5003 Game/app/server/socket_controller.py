"""
Socket controller - Main entry point for Socket.IO registration
"""
from app.server.socket_manager import SocketManager

#called by app.py; sets up socket ahndlers
def register_sockets(socketio):
    """Register all socket handlers using the SocketManager"""
    manager = SocketManager(socketio)
    return manager  #return manager