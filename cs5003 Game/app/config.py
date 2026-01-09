# app/config.py

import os

# SQLite file (same directory as main.py):
BASE_DIR = os.path.abspath(os.path.dirname(__file__) + "/..")
# game_data.db file
DB_FILE  = os.path.join(BASE_DIR, "app", "data", "game_data.db")


#clients send REST & Socket.IO
SERVER_URL = "http://127.0.0.1:5001"

## LACHLAN COMMENT: constants (i.e server port, secret keys etc.) -- put here :) ##
