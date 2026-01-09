import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import json
import tempfile
import sqlite3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import server modules
from app.controller.server_controller import register_routes
from app.server.socket_controller import register_sockets, game_manager
from app.model.db import init_db, get_db_connection
from app.shared.protocols import (
    LOGIN_ENDPOINT, REGISTER_ENDPOINT, PUZZLES_ENDPOINT, 
    PUZZLE_ENDPOINT, SUBMIT_RESULT, STATS_ENDPOINT
)

class TestServerController(unittest.TestCase):
    """Basic test cases for server REST API endpoints"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create Flask test client
        from flask import Flask
        from flask_socketio import SocketIO
        
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test Flask application
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['DB_FILE'] = self.db_path
        
        # Override DB_FILE in the app config
        import app.config
        self.original_db_file = app.config.DB_FILE
        app.config.DB_FILE = self.db_path
        
        # Initialize socketio
        self.socketio = SocketIO(self.app)
        
        # Register routes and sockets
        register_routes(self.app)
        register_sockets(self.socketio)
        
        # Initialize database
        init_db()
        
        # Create test client
        self.client = self.app.test_client()
        
        # Add test data
        self._add_test_data()
    
    def tearDown(self):
        """Clean up the test environment"""
        # Close and remove temporary database
        os.close(self.db_fd)
        os.unlink(self.db_path)
        
        # Restore original DB_FILE
        import app.config
        app.config.DB_FILE = self.original_db_file
    
    def _add_test_data(self):
        """Add test users and puzzle data"""
        conn = get_db_connection()
        
        # Add test user (check if already exists)
        existing_user = conn.execute("SELECT username FROM users WHERE username = ?", 
                                   ("testuser",)).fetchone()
        if not existing_user:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                ("testuser", "testpass")
            )
        
        # Add test puzzle (check if already exists)
        existing_puzzle = conn.execute("SELECT id FROM puzzles WHERE name = ?", 
                                    ("Test Puzzle",)).fetchone()
        if not existing_puzzle:
            grid = [["A", "B"], ["C", "D"]]
            clues_across = {"1": "First row", "2": "Second row"}
            clues_down = {"1": "First column", "2": "Second column"}
            answers = {"(0,0)": "A", "(0,1)": "B", "(1,0)": "C", "(1,1)": "D"}
            
            conn.execute(
                "INSERT INTO puzzles (name, grid, clues_across, clues_down, answers) VALUES (?, ?, ?, ?, ?)",
                (
                    "Test Puzzle",
                    json.dumps(grid),
                    json.dumps(clues_across),
                    json.dumps(clues_down),
                    json.dumps(answers)
                )
            )
        
        # Add test game statistics (check if already exists)
        existing_stat = conn.execute(
            "SELECT id FROM user_stats WHERE username = ? AND puzzle_id = ?", 
            ("testuser", 1)).fetchone()
        if not existing_stat:
            conn.execute(
                "INSERT INTO user_stats (username, puzzle_id, score, time_taken) VALUES (?, ?, ?, ?)",
                ("testuser", 1, 10, 300)
            )
        
        conn.commit()
        conn.close()
    
    def test_login(self):
        """Test user login functionality"""
        # Test successful login
        response = self.client.post(
            LOGIN_ENDPOINT,
            json={"username": "testuser", "password": "testpass"}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        
        # Test failed login
        response = self.client.post(
            LOGIN_ENDPOINT,
            json={"username": "testuser", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, 401)
    
    def test_register(self):
        """Test user registration functionality"""
        # Test successful registration
        unique_username = f"test_user_{os.urandom(4).hex()}"
        response = self.client.post(
            REGISTER_ENDPOINT,
            json={"username": unique_username, "password": "newpass"}
        )
        self.assertEqual(response.status_code, 201)
        
        # Test duplicate registration
        response = self.client.post(
            REGISTER_ENDPOINT,
            json={"username": "testuser", "password": "somepass"}
        )
        self.assertEqual(response.status_code, 409)
    
    def test_puzzles(self):
        """Test puzzle list and details functionality"""
        # Test puzzle list
        response = self.client.get(PUZZLES_ENDPOINT)
        self.assertEqual(response.status_code, 200)
        puzzles = json.loads(response.data)
        self.assertGreaterEqual(len(puzzles), 1)
        
        # Test puzzle details
        puzzle_id = 1
        response = self.client.get(PUZZLE_ENDPOINT.format(puzzle_id=puzzle_id))
        self.assertEqual(response.status_code, 200)
        puzzle = json.loads(response.data)
        self.assertIn("grid", puzzle)
        self.assertIn("clues_across", puzzle)
        self.assertIn("clues_down", puzzle)
    
    def test_stats(self):
        """Test user statistics functionality"""
        # Test retrieving statistics
        response = self.client.get(STATS_ENDPOINT.format(username="testuser"))
        self.assertEqual(response.status_code, 200)
        stats = json.loads(response.data)
        self.assertGreaterEqual(len(stats), 1)
        
        # Test submitting results
        response = self.client.post(
            SUBMIT_RESULT,
            json={
                "username": "testuser",
                "puzzle_id": 1,
                "score": 8,
                "time": 240
            }
        )
        self.assertEqual(response.status_code, 201)


class TestSocketController(unittest.TestCase):
    """Simplified test cases for Socket.IO functionality"""
    
    def setUp(self):
        """Set up the test environment"""
        from flask import Flask
        from flask_socketio import SocketIO
        
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test Flask application
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['DB_FILE'] = self.db_path
        
        # Override DB_FILE in the app config
        import app.config
        self.original_db_file = app.config.DB_FILE
        app.config.DB_FILE = self.db_path
        
        # Initialize database
        init_db()
        
        # Mock game manager to avoid background task issues
        from app.server import socket_controller
        from app.server.game_logic import GameManager
        self.original_game_manager = socket_controller.game_manager
        mock_game_manager = MagicMock(spec=GameManager)
        mock_game_manager.create_new_game.return_value = "test_game_1"
        socket_controller.game_manager = mock_game_manager
        
        # Create socketio instance
        self.socketio = SocketIO(self.app)
        register_sockets(self.socketio)
        
        # Create test client
        self.client = self.socketio.test_client(self.app)
    
    def tearDown(self):
        """Clean up the test environment"""
        # Close and remove temporary database
        os.close(self.db_fd)
        os.unlink(self.db_path)
        
        # Restore original DB_FILE
        import app.config
        app.config.DB_FILE = self.original_db_file
        
        # Restore original game_manager
        if self.original_game_manager is not None:
            from app.server import socket_controller
            socket_controller.game_manager = self.original_game_manager
        
        # Disconnect client
        if hasattr(self, 'client') and self.client.is_connected():
            try:
                self.client.disconnect()
            except RuntimeError:
                pass
    
    def test_socket_connection(self):
        """Test Socket connection"""
        # Check if client is connected
        self.assertTrue(self.client.is_connected())
    
    def test_create_game(self):
        """Test game creation"""
        # Send create_game event
        self.client.emit('create_game', {"puzzle_id": 1, "username": "testuser"})
        
        # Receive response
        response = self.client.get_received()
        
        # Look for game_created events
        game_created_events = [
            event for event in response 
            if event['name'] == 'game_created'
        ]
        
        # Should receive a game_created event
        self.assertGreaterEqual(len(game_created_events), 1)


if __name__ == '__main__':
    unittest.main()
