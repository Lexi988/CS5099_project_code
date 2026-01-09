# #!/usr/bin/env python3
# # app/legacy/seed_sample_db.py

# # IMPORT libs
# from pathlib import Path
# import sqlite3
# from app.config import DB_FILE

# ### REFS:
# # URL: Create db code adapted from https://stackoverflow.com/a/27298043
# # by Aaron Hall (stackoverflow.com/users/541136/aaron-hall)
# #
# # URL: Create SQLite db code taken from:
# # https://www.ionos.co.uk/digitalguide/websites/web-development/sqlite3-python/

# def init_db():
#     with sqlite3.connect(DB_FILE) as conn:
#         cursor = conn.cursor()

#         # Create user_accounts table
#         cursor.execute(
#             """
#             CREATE TABLE IF NOT EXISTS user_accounts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT UNIQUE NOT NULL,
#                 password TEXT NOT NULL
#             );
#             """
#         )

#         # Create puzzles table
#         cursor.execute(
#             """
#             CREATE TABLE IF NOT EXISTS puzzles (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT NOT NULL,
#                 grid TEXT,
#                 clues_across TEXT,
#                 clues_down TEXT,
#                 answers TEXT
#             );
#             """
#         )

#         # Create user_stats table
#         cursor.execute(
#             """
#             CREATE TABLE IF NOT EXISTS user_stats (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT NOT NULL,
#                 puzzle_id INTEGER NOT NULL,
#                 score INTEGER,
#                 time_taken INTEGER,
#                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#             );
#             """
#         )

#         conn.commit()


# if __name__ == "__main__":
#     # 1) Create tables (if they don’t already exist)
#     init_db()

#     # 2) Insert a sample puzzle
#     import json

#     sample_puzzle = {
#         "name": "Test Puzzle",
#         "grid": [
#             ["H", "E", "L", "L", "O"],
#             ["",  "",  "",  "",  "A"],
#             ["W", "O", "R", "L", "D"],
#             ["",  "",  "",  "",  "E"],
#             ["",  "",  "",  "",  "S"]
#         ],
#         "clues_across": {1: "Greeting", 3: "Planet"},
#         "clues_down":   {1: "First letter of hello", 5: "Vowel stack"},
#         "answers": {
#             "0,0": "H", "0,1": "E", "0,2": "L", "0,3": "L", "0,4": "O",
#             "1,4": "A",
#             "2,0": "W", "2,1": "O", "2,2": "R", "2,3": "L", "2,4": "D",
#             "3,4": "E",
#             "4,4": "S"
#         }
#     }

#     with sqlite3.connect(DB_FILE) as conn:
#         c = conn.cursor()
#         c.execute(
#             "INSERT INTO puzzles (name, grid, clues_across, clues_down, answers) VALUES (?, ?, ?, ?, ?)",
#             (
#                 sample_puzzle["name"],
#                 json.dumps(sample_puzzle["grid"]),
#                 json.dumps(sample_puzzle["clues_across"]),
#                 json.dumps(sample_puzzle["clues_down"]),
#                 json.dumps(sample_puzzle["answers"])
#             )
#         )
#         conn.commit()