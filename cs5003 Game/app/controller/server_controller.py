# app/controller/server_controller.py
"""
Server controller

This file defines:
register_routes(app); attaches every REST end point
create_app(testing=False) 


REFS:

#Flask, “Welcome to Flask — Flask Documentation (3.0.x),” Palletsprojects.com, 2010.
#  https://flask.palletsprojects.com/en/stable/ (accessed Apr. 12, 2025). 

routing pattern adapted from
https://www.digitalocean.com/community/tutorials/how-to-create-your-first-web-application-using-flask-and-python-3

 “SQLite Databases With Python - Full Course,” 
 YouTube. May 12, 2020. Accessed: Apr. 12, 2025. 
 [YouTube Video]. Available: https://www.youtube.com/watch?v=byHcYRpMgI4

app-factory logic adapted from:
https://flask.palletsprojects.com/en/stable/patterns/appfactories/
https://www.youtube.com/watch?v=EgpLj86ZHFQ 'Please Learn How To Write Tests in Python… • Pytest Tutorial' by Tech with Tim



"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO

import requests
import sqlite3
from app.config import DB_FILE

#project modules
from app.shared.protocols import (
    LOGIN_ENDPOINT, REGISTER_ENDPOINT,
    PUZZLES_ENDPOINT, PUZZLE_ENDPOINT,
    ADD_PUZZLE, SUBMIT_RESULT, STATS_ENDPOINT,
    # Social endpoints
    SEARCH_USERS_ENDPOINT, FRIEND_REQUEST_ENDPOINT,
    ACCEPT_FRIEND_ENDPOINT, REJECT_FRIEND_ENDPOINT,
    FRIENDS_LIST_ENDPOINT, MESSAGES_ENDPOINT,
    SEND_MESSAGE_ENDPOINT, UNREAD_COUNT_ENDPOINT
)
from app.model.db import (
    init_db, create_user, verify_user,
    get_puzzles, get_puzzle, add_puzzle,
    submit_result, get_stats,
    # Social DB functions
    send_friend_request, accept_friend_request,
    reject_friend_request, get_friends, get_friend_requests,
    send_message, get_messages, get_unread_message_count
)

from app.server.socket_controller import register_sockets


#REST routes
def register_routes(app: Flask) -> None:
    """Attach all Flask routes to *app* and make sure the DB exists once."""
    init_db()

    #auth.
    @app.route(LOGIN_ENDPOINT, methods=["POST"])
    def login():
        data = request.json  # Get the JSON data from the request
        if verify_user(data["username"], data["password"]):
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

    @app.route(REGISTER_ENDPOINT, methods=["POST"])
    def register():
        data = request.json
        if create_user(data["username"], data["password"]):
            return jsonify({"status": "success"}), 201
        return jsonify({"status": "fail", "message": "Username exists"}), 409

    @app.route("/")
    def home():
        return "Flask is running!"

    @app.route("/download-puz")
    def download_puz():
        # Download puzzle
        url = "http://herbach.dnsalias.com/uc/uc230505.puz"
        filename = "daily.puz"
        response = requests.get(url)
        with open(filename, "wb") as f:
            f.write(response.content)

        import puz
        # Read puzzle with puzpy
        puzzle = puz.read(filename)
        title = puzzle.title
        author = puzzle.author
        clues = "\n".join(puzzle.clues)

        # Save to SQLite
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO puzzles (name, grid, clues_across, clues_down, answers)
            VALUES (?, ?, ?, ?, ?)
        """, (title, "", clues, "", ""))
        conn.commit()
        conn.close()

        return f"""
            ✅ Puzzle downloaded and saved to database!<br>
            <strong>Title:</strong> {title}<br>
            <strong>Author:</strong> {author}<br>
            <strong>Clues saved:</strong> {len(puzzle.clues)}
        """

    #puzzles
    @app.route(PUZZLES_ENDPOINT, methods=["GET"])
    def list_puzzles():
        return jsonify(
            [{"id": pid, "name": name} for pid, name in get_puzzles()]
        )

    @app.route(PUZZLE_ENDPOINT.format(puzzle_id="<int:puzzle_id>"), methods=["GET"])
    def fetch_puzzle(puzzle_id):
        p = get_puzzle(puzzle_id)
        if not p:
            return jsonify({"error": "Not found"}), 404
        return jsonify(p)

    @app.route(ADD_PUZZLE, methods=["POST"])
    def upload_puzzle():
        d = request.json
        add_puzzle(d["name"], d["grid"],
                   d["clues_across"], d["clues_down"], d["answers"])
        return jsonify({"status": "success"}), 201

    #results / stats
    @app.route(SUBMIT_RESULT, methods=["POST"])
    def result():
        d = request.json
        submit_result(d["username"], d["puzzle_id"], d["score"], d["time"])
        return jsonify({"status": "success"}), 201

    @app.route(STATS_ENDPOINT.format(username="<username>"), methods=["GET"])
    def stats(username):
        return jsonify(get_stats(username))
    
    # Social Features API Routes
    @app.route(SEARCH_USERS_ENDPOINT, methods=["GET"])
    def search_users():
        query = request.args.get("q", "")
        users = []  # 这里应该有一个函数来搜索用户，但在db.py中似乎没有定义
        return jsonify({"users": users})
    
    @app.route(FRIEND_REQUEST_ENDPOINT, methods=["POST"])
    def friend_request():
        d = request.json
        result = send_friend_request(d["from_user"], d["to_user"])
        if result:
            return jsonify({"status": "success"}), 201
        return jsonify({"status": "failed", "message": "Request failed or already friends"}), 409
    
    @app.route(ACCEPT_FRIEND_ENDPOINT, methods=["POST"])
    def accept_friend():
        d = request.json
        result = accept_friend_request(d["from_user"], d["to_user"])
        if result:
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "failed", "message": "Failed to accept"}), 400
    
    @app.route(REJECT_FRIEND_ENDPOINT, methods=["POST"])
    def reject_friend():
        d = request.json
        result = reject_friend_request(d["from_user"], d["to_user"])
        if result:
            return jsonify({"status": "success"}), 200
        return jsonify({"status": "failed", "message": "Failed to reject"}), 400
    
    @app.route(FRIENDS_LIST_ENDPOINT, methods=["GET"])
    def friends_list():
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        friends = get_friends(username)
        requests = get_friend_requests(username)
        return jsonify({"friends": friends, "requests": requests})
    
    @app.route(MESSAGES_ENDPOINT.format(username="<username>"), methods=["GET"])
    def get_chat_history(username):
        current_user = request.args.get("current_user")
        if not current_user:
            return jsonify({"error": "Current user required"}), 400
        
        messages = get_messages(current_user, username)
        return jsonify(messages)
    
    @app.route(SEND_MESSAGE_ENDPOINT, methods=["POST"])
    def handle_send_message():
        d = request.json
        result = send_message(d["sender"], d["receiver"], d["content"])
        if result:
            return jsonify({"status": "success"}), 201
        return jsonify({"status": "failed", "message": "Failed to send message"}), 400
    
    @app.route(UNREAD_COUNT_ENDPOINT, methods=["GET"])
    def unread_count():
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "Username required"}), 400
        
        count = get_unread_message_count(username)
        return jsonify({"count": count})

### NOTE for Ch-D
# def _open_nyt_puzzle():
"""TO DO: add puzzle APIs i.e. NYT puzzles"""
#     pass


#app-factory for pytest & main.py
def create_app(testing: bool = False):
    """
    Build server without running;unit-tests can spin up
    isolated app
    """
    app = Flask(__name__)
    app.config.from_object("app.config")
    if testing:
        app.config["TESTING"] = True

    socketio = SocketIO(app, cors_allowed_origins="*")
    register_routes(app)
    register_sockets(socketio)
    app.socketio = socketio        # let rest of code reach

    if testing:                   
        return app

    return app, socketio       
     

    
