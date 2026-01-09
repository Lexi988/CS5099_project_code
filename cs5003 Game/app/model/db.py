#/app/model/db.py

"""
This module manages SQLite database interactions for crossword puzzle app
db setup, usr management, puzzle management, stats track, multiplayer functions
"""

import sqlite3
import json

from app.config import DB_FILE


#set up db connection
def get_db_connection():
    """
    Create and return SQLite connection
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ Init. all necessary tables if don't already exist: """
    conn = get_db_connection()
    c = conn.cursor()


    #ratings table
    c.execute('''CREATE TABLE IF NOT EXISTS puzzle_ratings
                 (id INTEGER PRIMARY KEY,
                  puzzle_id INTEGER,
                  username TEXT,
                  rating INTEGER,
                  comment TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (puzzle_id) REFERENCES puzzles(id),
                  UNIQUE(puzzle_id, username))''')

    #usrs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)

    #puzzles table
    c.execute("""
        CREATE TABLE IF NOT EXISTS puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grid TEXT,
            clues_across TEXT,
            clues_down TEXT,
            answers TEXT
        )
    """)

    # statstable
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            puzzle_id INTEGER NOT NULL,
            score INTEGER,
            time_taken INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(username) REFERENCES users(username),
            FOREIGN KEY(puzzle_id) REFERENCES puzzles(id)
        )
    """)

    #multiplayer sessions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_sessions (
            game_id TEXT PRIMARY KEY,
            puzzle_id INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(puzzle_id) REFERENCES puzzles(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS game_players (
            game_id TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (game_id, username),
            FOREIGN KEY(game_id) REFERENCES game_sessions(game_id),
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1 TEXT NOT NULL,
            user2 TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user1) REFERENCES users(username),
            FOREIGN KEY(user2) REFERENCES users(username),
            UNIQUE(user1, user2)
        )
    """)
    

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            read INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sender) REFERENCES users(username),
            FOREIGN KEY(receiver) REFERENCES users(username)
        )
    """)
    
    # Activity feed table
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            related_id INTEGER,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user) REFERENCES users(username)
        )
    """)

    conn.commit()
    conn.close()


#user management

def create_user(username, password):
    """
    Insert a new user. Returns False usrname duplicate
    """
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            (username, password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True

def verify_user(username, password):
    """
    Check credentials. Returns True if matching user is found.
    """
    row = get_db_connection().execute(
        "SELECT 1 FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    return bool(row)


#puzzle Management

def get_puzzles():
    """
    Return list for all puzzles
    """
    rows = get_db_connection().execute(
        "SELECT id, name FROM puzzles"
    ).fetchall()
    return [(r["id"], r["name"]) for r in rows]

def get_puzzle(puzzle_id):
    """
    Load a single puzzle's full data by ID, or none if not found
    """
    row = get_db_connection().execute(
        "SELECT * FROM puzzles WHERE id=?", (puzzle_id,)
    ).fetchone()
    if not row:
        return None

    return {
        "id":           row["id"],
        "name":         row["name"],
        "grid":         json.loads(row["grid"]),
        "clues_across": json.loads(row["clues_across"]),
        "clues_down":   json.loads(row["clues_down"]),
        "answers":      json.loads(row["answers"])
    }

def add_puzzle(name, grid, clues_across, clues_down, answers):
    """
    Insert new puzzle; JSON: grid/clues/answers for storing
    """
    conn = get_db_connection()
    cursor = conn.execute("""
        INSERT INTO puzzles (name,grid,clues_across,clues_down,answers)
        VALUES (?,?,?,?,?)
    """, (
        name,
        json.dumps(grid),
        json.dumps(clues_across),
        json.dumps(clues_down),
        json.dumps(answers),
    ))
    puzzle_id = cursor.lastrowid
    
    #record this activity if we know who created it
    #info not currently passed to function; could be added in a future update :)
    
    conn.commit()
    conn.close()
    return True

def delete_puzzle(puzzle_id):
    """
    Delete a puzzle by ID
    Returns True if successful, False if no rows affected
    """
    conn = get_db_connection()
    
    # Delete puzzle stats first (foreign key constraint)
    conn.execute("DELETE FROM user_stats WHERE puzzle_id = ?", (puzzle_id,))
    
    # Delete activities related to this puzzle
    conn.execute("DELETE FROM activities WHERE related_id = ? AND activity_type = 'completed_puzzle'", (puzzle_id,))
    
    # Delete game sessions for this puzzle
    game_sessions = conn.execute(
        "SELECT game_id FROM game_sessions WHERE puzzle_id = ?", 
        (puzzle_id,)
    ).fetchall()
    
    for session in game_sessions:
        game_id = session["game_id"]
        conn.execute("DELETE FROM game_players WHERE game_id = ?", (game_id,))
    
    conn.execute("DELETE FROM game_sessions WHERE puzzle_id = ?", (puzzle_id,))
    
    # Finally delete the puzzle itself
    cursor = conn.execute("DELETE FROM puzzles WHERE id = ?", (puzzle_id,))
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success


#stat. track

def submit_result(username, puzzle_id, score, time_taken):
    """ Record 1 completion of a puzzle by usr """
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO user_stats (username,puzzle_id,score,time_taken)
        VALUES (?,?,?,?)
    """, (username, puzzle_id, score, time_taken))
    
    puzzle_name = get_db_connection().execute(
        "SELECT name FROM puzzles WHERE id=?", (puzzle_id,)
    ).fetchone()["name"]
    
    details = json.dumps({
        "puzzle_id": puzzle_id,
        "puzzle_name": puzzle_name,
        "score": score,
        "time_taken": time_taken
    })
    
    conn.execute("""
        INSERT INTO activities (user, activity_type, related_id, details)
        VALUES (?, 'completed_puzzle', ?, ?)
    """, (username, puzzle_id, details))
    
    conn.commit()
    conn.close()

def get_stats(username):
    """
    Fetch all stats for a given user, most recent first
    return list of tuples: puzzle_name, score, time_taken, timestamp
    """
    rows = get_db_connection().execute("""
        SELECT p.name, s.score, s.time_taken, s.timestamp
        FROM user_stats s
        JOIN puzzles p ON s.puzzle_id = p.id
        WHERE s.username = ?
        ORDER BY s.timestamp DESC
    """, (username,)).fetchall()

    return [
        (r["name"], r["score"], r["time_taken"], r["timestamp"])
        for r in rows
    ]

def rec_activity(limit=50):
    """
    This will return the most recent puzzle completion with username, description and timestamp tuples.
    """
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT s.username,
               p.name      AS puzzle_name,
               s.time_taken,
               s.timestamp
        FROM user_stats s
        JOIN puzzles p ON s.puzzle_id = p.id
        ORDER BY s.timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    activity = []
    for r in rows:
        mins = r["time_taken"] // 60
        secs = r["time_taken"] % 60
        desc = f'solved "{r["puzzle_name"]}" in {mins}m{secs}s'
        activity.append((r["username"], desc, r["timestamp"]))

    return activity


#multiplayer functions

def create_game_session(game_id, puzzle_id):
    """
    create a new multiplayer session in the DB
    """
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO game_sessions (game_id, puzzle_id, status) VALUES (?, ?, ?)",
        (game_id, puzzle_id, "active")
    )
    conn.commit()
    conn.close()

def add_player_to_game(game_id, username):
    """
    Add user to an existing game sesh
    """
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO game_players (game_id, username) VALUES (?, ?)",
            (game_id, username)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def get_active_games():
    rows = get_db_connection().execute("""
        SELECT g.game_id, p.name, COUNT(gp.username) AS players
        FROM game_sessions g
        JOIN puzzles p ON g.puzzle_id = p.id
        LEFT JOIN game_players gp ON g.game_id = gp.game_id
        WHERE g.status = 'active'
        GROUP BY g.game_id
    """).fetchall()

    return [
        (r["game_id"], r["name"], r["players"])
        for r in rows
    ]

def update_game_status(game_id, status):
    """
    Change a game's status field (such as 'completed')
    """
    conn = get_db_connection()
    conn.execute(
        "UPDATE game_sessions SET status = ? WHERE game_id = ?",
        (status, game_id)
    )
    conn.commit()
    conn.close()

#社交功能

def send_friend_request(from_user, to_user):
    """
    Send a friend request, status is "pending"
    Returns False if relationship already exists, otherwise True
    """
    conn = get_db_connection()
    try:
        # Check if friend relationship already exists (in either direction)
        existing = conn.execute("""
            SELECT 1 FROM friends 
            WHERE (user1=? AND user2=?) OR (user1=? AND user2=?)
        """, (from_user, to_user, to_user, from_user)).fetchone()
        
        if existing:
            conn.close()
            return False
            
        conn.execute("""
            INSERT INTO friends (user1, user2, status)
            VALUES (?, ?, 'pending')
        """, (from_user, to_user))
        
        # Record this as an activity
        details = json.dumps({"to_user": to_user})
        conn.execute("""
            INSERT INTO activities (user, activity_type, details)
            VALUES (?, 'friend_request', ?)
        """, (from_user, details))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error sending friend request: {e}")
        conn.close()
        return False

def accept_friend_request(from_user, to_user):
    """
    Accept a friend request, updating status to "accepted" 
    """
    conn = get_db_connection()
    result = conn.execute("""
        UPDATE friends 
        SET status='accepted' 
        WHERE user1=? AND user2=? AND status='pending'
    """, (from_user, to_user)).rowcount
    
    if result > 0:
        # Record this as an activity for both users
        details_from = json.dumps({"friend": to_user})
        details_to = json.dumps({"friend": from_user})
        
        conn.execute("""
            INSERT INTO activities (user, activity_type, details)
            VALUES (?, 'new_friend', ?)
        """, (from_user, details_from))
        
        conn.execute("""
            INSERT INTO activities (user, activity_type, details)
            VALUES (?, 'new_friend', ?)
        """, (to_user, details_to))
    
    conn.commit()
    conn.close()
    return result > 0

def get_friend_requests(username):
    """
    Get pending friend requests sent to the user
    """
    rows = get_db_connection().execute("""
        SELECT user1, created_at 
        FROM friends 
        WHERE user2=? AND status='pending'
        ORDER BY created_at DESC
    """, (username,)).fetchall()
    
    return [(r["user1"], r["created_at"]) for r in rows]

def get_friends(username):
    """
    Get all accepted friends for a user
    """
    rows = get_db_connection().execute("""
        SELECT 
            CASE 
                WHEN user1=? THEN user2 
                ELSE user1 
            END as friend
        FROM friends 
        WHERE (user1=? OR user2=?) AND status='accepted'
    """, (username, username, username)).fetchall()
    
    return [r["friend"] for r in rows]

def send_message(sender, receiver, content):
    """
    Send a message, returns the message ID
    """
    conn = get_db_connection()
    cursor = conn.execute("""
        INSERT INTO messages (sender, receiver, content)
        VALUES (?, ?, ?)
    """, (sender, receiver, content))
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id

def get_messages(user1, user2, limit=50):
    """
    Get recent messages between two users
    """
    rows = get_db_connection().execute("""
        SELECT id, sender, receiver, content, read, timestamp
        FROM messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user1, user2, user2, user1, limit)).fetchall()
    
    return [{
        "id": r["id"],
        "sender": r["sender"],
        "receiver": r["receiver"],
        "content": r["content"],
        "read": bool(r["read"]),
        "timestamp": r["timestamp"]
    } for r in rows]

def mark_messages_as_read(receiver, sender):
    """
    Mark all messages from a specific sender as read
    """
    conn = get_db_connection()
    conn.execute("""
        UPDATE messages
        SET read=1
        WHERE sender=? AND receiver=? AND read=0
    """, (sender, receiver))
    conn.commit()
    conn.close()

def get_unread_message_count(username):
    """
    Get the count of unread messages for a user
    """
    row = get_db_connection().execute("""
        SELECT COUNT(*) as count
        FROM messages
        WHERE receiver=? AND read=0
    """, (username,)).fetchone()
    
    return row["count"] if row else 0

def reject_friend_request(from_user, to_user):
    """
    Reject a friend request, deleting it from the database
    """
    conn = get_db_connection()
    result = conn.execute("""
        DELETE FROM friends 
        WHERE user1=? AND user2=? AND status='pending'
    """, (from_user, to_user)).rowcount
    conn.commit()
    conn.close()
    return result > 0

# Activity feed functions

def get_friend_activities(username, limit=20):
    """
    Get recent activities from a user's friends
    Returns a list of activity records ordered by time (newest first)
    """
    conn = get_db_connection()
    
    # First get the user's friends
    friends = get_friends(username)
    
    if not friends:
        return []
    
    # Build a query with placeholders for all friends
    placeholders = ','.join(['?'] * len(friends))
    
    # Get activities from these friends
    query = f"""
        SELECT a.id, a.user, a.activity_type, a.related_id, a.details, a.timestamp
        FROM activities a
        WHERE a.user IN ({placeholders})
        ORDER BY a.timestamp DESC
        LIMIT ?
    """
    
    # Add the limit parameter to the friends list
    params = friends + [limit]
    
    rows = conn.execute(query, params).fetchall()
    
    activities = []
    for row in rows:
        activity = {
            "id": row["id"],
            "user": row["user"],
            "activity_type": row["activity_type"],
            "related_id": row["related_id"],
            "details": json.loads(row["details"]) if row["details"] else {},
            "timestamp": row["timestamp"]
        }
        activities.append(activity)
    
    conn.close()
    return activities

def format_activity_message(activity):
    """
    Format an activity record into a human-readable message
    """
    user = activity["user"]
    activity_type = activity["activity_type"]
    details = activity["details"]
    
    if activity_type == "completed_puzzle":
        puzzle_name = details.get("puzzle_name", "a puzzle")
        score = details.get("score", 0)
        time_taken = details.get("time_taken", 0)
        minutes, seconds = divmod(time_taken, 60)
        return f"{user} completed '{puzzle_name}' with a score of {score} in {minutes}m {seconds}s"
    
    elif activity_type == "new_friend":
        friend = details.get("friend", "someone")
        return f"{user} became friends with {friend}"
    
    elif activity_type == "friend_request":
        to_user = details.get("to_user", "someone")
        return f"{user} sent a friend request to {to_user}"
    
    # Default case
    return f"{user} did something"



#functions for ratings
def rate_puzzle(puzzle_id, username, rating, comment=""):
    """Rate a puzzle from 1-5 stars with optional comment."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    #check usr has already rated this puzzle
    c.execute('''SELECT id FROM puzzle_ratings 
                 WHERE puzzle_id = ? AND username = ?''', 
              (puzzle_id, username))
    existing = c.fetchone()
    
    if existing:
        # Update existing rating
        c.execute('''UPDATE puzzle_ratings 
                     SET rating = ?, comment = ?, timestamp = CURRENT_TIMESTAMP 
                     WHERE puzzle_id = ? AND username = ?''', 
                  (rating, comment, puzzle_id, username))
    else:
        # Insert new rating
        c.execute('''INSERT INTO puzzle_ratings 
                     (puzzle_id, username, rating, comment)
                     VALUES (?, ?, ?, ?)''', 
                  (puzzle_id, username, rating, comment))
    
    conn.commit()
    conn.close()
    return True

def get_puzzle_ratings(puzzle_id):
    """ratings for puzzle"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''SELECT username, rating, comment, timestamp 
                 FROM puzzle_ratings 
                 WHERE puzzle_id = ?
                 ORDER BY timestamp DESC''', 
              (puzzle_id,))
    ratings = c.fetchall()
    
    #ave. rating
    c.execute('''SELECT AVG(rating) FROM puzzle_ratings 
                 WHERE puzzle_id = ?''', 
              (puzzle_id,))
    avg_rating = c.fetchone()[0]
    
    conn.close()
    
    return {
        "ratings": ratings,
        "average": avg_rating or 0,
        "count": len(ratings)
    }


def get_last_inserted_puzzle_id():
    """
    ID of the most recent puzzle in db"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT id FROM puzzles ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    
    conn.close()
    
    return result[0] if result else None

# def submit_rating():
#     try:
#         rating = rating_var.get()
#         comment = comment_text.get("1.0", tk.END).strip()
#         success = rate_puzzle(self.puzzle["id"], self.username, rating, comment)
#         if success:
#             messagebox.showinfo("Thank You", "Your rating has been submitted!")
#             rating_dialog.destroy()
#         else:
#             messagebox.showerror("Error", "Failed to submit rating. Please try again.")
#     except Exception as e:
#         messagebox.showerror("Error", f"An error occurred: {str(e)}")