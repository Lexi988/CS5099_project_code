"""
game Manager for the Crossword Server

this module handles management of crossword game instances
and coordinates multiplayer interactions
"""

import threading
import time
import uuid
from flask_socketio import SocketIO
from app.model.db import create_game_session, update_game_status
from app.shared.protocols import SOCKET_EVENTS

class GameManager:
    """
    manages crossword game instances player sessions
    """
    
    def __init__(self):
        self.socketio = None      # set in run_server()
        self.active_games = {}    #dict. stores active game sessions
        self.player_sessions = {} #dict. tracks player connections
        self.lock = threading.Lock()
    
    def bind(self, socketio: SocketIO):
        """called by run_server() to give us the Socketio instance"""
        self.socketio = socketio
    
    def create_new_game(self, data):
        """create new game instance with puzz data"""
        game_id = str(uuid.uuid4())
        puzzle_id = data["puzzle_id"]
        
        with self.lock:
            self.active_games[game_id] = {
                "players": [], 
                "time_left": 300, 
                "active": True
            }
        
        # Record in database
        create_game_session(game_id, puzzle_id)
        
        # Start timer task on SocketIO's event loop
        self.socketio.start_background_task(self._game_loop, game_id)
        return game_id
    
    def add_player(self, game_id, username):
        """Addplayer to game"""
        with self.lock:
            self.active_games[game_id]["players"].append(username)
            
        # Also record in DB
        from app.model.db import add_player_to_game
        add_player_to_game(game_id, username)
    
    def _game_loop(self, game_id):
        """timer ticks until time runs out"""
        while True:
            time.sleep(1)
            with self.lock:
                game = self.active_games.get(game_id)
                if not game or not game["active"]:
                    break
                game["time_left"] -= 1
                t = game["time_left"]

            # Emit game_timer event
            self.socketio.emit(
                SOCKET_EVENTS["GAME_TIMER"],
                {"time": t},
                room=game_id
            )

            if t <= 0:
                with self.lock:
                    game["active"] = False
                self.socketio.emit(
                    SOCKET_EVENTS["GAME_OVER"],
                    {"reason": "time_up"},
                    room=game_id
                )
                break

        #mark sesh completed in db
        update_game_status(game_id, "completed")