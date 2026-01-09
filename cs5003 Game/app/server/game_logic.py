# app/server/game_logic.py

import threading
import time
import uuid

from flask_socketio import SocketIO
from app.model.db import create_game_session, update_game_status
from app.shared.protocols import SOCKET_EVENTS 

class GameManager:
    def __init__(self):
        self.socketio     = None      # set in run_server()
        self.active_games = {}
        self.lock         = threading.Lock()

    def bind(self, socketio: SocketIO):
        """Called by run_server() to give us the SocketIO instance"""
        self.socketio = socketio

    def create_new_game(self, data):
        game_id   = str(uuid.uuid4())
        puzzle_id = data["puzzle_id"]

        with self.lock:
            self.active_games[game_id] = {
                "players": [], "time_left": 300, "active": True
            }

        #go to DB
        create_game_session(game_id, puzzle_id)
        #start timer task on SocketIO’s event loop
        self.socketio.start_background_task(self._game_loop, game_id)
        return game_id

    def add_player(self, game_id, username):
        with self.lock:
            self.active_games[game_id]["players"].append(username)
        #also record in DB
        from app.model.db import add_player_to_game
        add_player_to_game(game_id, username)

    def _game_loop(self, game_id):
        """Emits timer ticks until time runs out."""
        while True:
            time.sleep(1)
            with self.lock:
                game = self.active_games.get(game_id)
                if not game or not game["active"]:
                    break
                game["time_left"] -= 1
                t = game["time_left"]

            # emit game_timer event
            self.socketio.emit(
                SOCKET_EVENTS["GAME_TIMER"],
                {"time": t},
                room=game_id
            )

            if t <= 0:
                with self.lock:
                    game["active"] = False
                # emit a game_over event
                self.socketio.emit(
                    SOCKET_EVENTS["GAME_OVER"],
                    {"reason": "time_up"},
                    room=game_id
                )
                break

        # mark session completed in DB
        update_game_status(game_id, "completed")
