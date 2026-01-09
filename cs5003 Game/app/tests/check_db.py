import sqlite3
import os

# Hardcode the path to make sure we're checking the right file
DB_FILE = "/Users/lachlan/Documents/Uni/CS5003/p3/p3_cs5003_g4/app/data/game_data.db"

print(f"Checking database at: {DB_FILE}")
print(f"File exists: {os.path.exists(DB_FILE)}")

try:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Check tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    print(f"Tables in database: {tables}")
    
    # Check users
    try:
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        print(f"Users in database: {users}")
    except sqlite3.OperationalError as e:
        print(f"Error checking users table: {e}")
    
    conn.close()
except Exception as e:
    print(f"Error connecting to database: {e}")