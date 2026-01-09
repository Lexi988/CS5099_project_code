"""
Client controller for the Crossword app.
Handles user interface flow, server comms, 
and coords between views + model ops """

import requests
import socketio
from tkinter import messagebox
from app.utils.puzzle_downloader import download_and_save_puzzle
from app.model.db import get_last_inserted_puzzle_id


# Model imports
from app.model.db import (
    get_puzzles, get_puzzle, add_puzzle as db_add_puzzle, delete_puzzle,
    submit_result, get_stats, get_active_games, rec_activity, get_friend_activities
)
from app.config import SERVER_URL
from app.shared.protocols import ADD_PUZZLE_ENDPOINT as ADD_PUZZLE

# View imports
from app.view.login_view          import LoginView
from app.view.menu_view           import MenuView
from app.view.puzzle_view         import PuzzleView
from app.view.editor_view         import EditorView          # advanced editor
from app.view.simple_creator_view import SimpleCreatorView   # quick create
from app.view.stats_view          import StatsView           # NEW stats screen
from app.view.feed_view           import FeedView

# Create Socket.io client connection
sio = socketio.Client()

#track completed puzzles (from legacy client.py)
_puzzles_solved = 0

# entry called from - main.py
def launch_application(root):
    """show the login/registration screen"""
    LoginView(root, on_success=_on_login)

#login main menu
def _on_login(root, username):
    """User logged-in successfully – show main menu."""
    print(f"DEBUG: _on_login called with username: {username}")
    # Try to connect to Socket.io server
    try:
        if not sio.connected:
            sio.connect(SERVER_URL)
            print("Connected to Socket.io server")
    except Exception as e:
        print(f"Unable to connect to Socket.io server: {e}")
    
    # Get active games
    active_games = get_active_games()
    
    # Init. menu view with proper parameters
    menu_view = MenuView(
        root, username,
        play_callback   = lambda: _choose_puzzle(root, username),
        stats_callback  = lambda: get_stats(username),  # Return statistics data directly
        add_callback    = lambda: _add_puzzle(root),    # Advanced editor
        quit_callback   = root.quit,
        nyt_callback    = lambda: _open_nyt_puzzle(root, username),  # Pass root and username 
        quick_callback  = lambda: _quick_create(root),
        # feed_callback   = lambda: _show_activity_feed(root),  
        active_games    = active_games
    )


# menu button handlers
def _choose_puzzle(root, username):
    puzzles = get_puzzles()

    def _start(puzzle_id):
        puzzle = get_puzzle(puzzle_id)
        PuzzleView(root, username, puzzle)
        
    def _delete(puzzle_id):
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion", 
            "Are you sure you want to delete this puzzle? This action cannot be undone."
        )
        
        if confirm:
            success = delete_puzzle(puzzle_id)
            if success:
                messagebox.showinfo("Success", "Puzzle deleted successfully.")
                # Refresh the puzzle list
                _choose_puzzle(root, username)
            else:
                messagebox.showerror("Error", "Failed to delete puzzle.")

    #reuse helper in MenuView
    MenuView.clear_and_show_puzzles(root, puzzles, _start, _delete)


def _show_stats(root, username):
    """Display the statistics screen with activity feed."""
    # Get statistics data
    stats = get_stats(username)
         
    # Get friend activity data
    activities = get_friend_activities(username)
    
    # Clear current window content
    for widget in root.winfo_children():
        widget.destroy()
    
    # Use MenuView's method to display statistics and activity data
    from app.view.menu_view import MenuView
    menu_view = MenuView(
        root, username,
        play_callback=lambda: _choose_puzzle(root, username),
        stats_callback=lambda: stats,
        add_callback=lambda: _add_puzzle(root),
        quit_callback=root.quit,
        nyt_callback=lambda: _open_nyt_puzzle(root, username),  # Pass root and username
        quick_callback=lambda: _quick_create(root),
        active_games=get_active_games()
    )
    menu_view._show_stats_and_activities(stats, activities)


def _add_puzzle(root):
    """launch adv. create, then POST puzzle to server."""
    def on_submit(name, grid, across, down, answers):
        try:
            response = requests.post(
                SERVER_URL + ADD_PUZZLE,
                json={
                    "name": name,
                    "grid": grid,
                    "clues_across": across,
                    "clues_down": down,
                    "answers": answers
                }
            )
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Puzzle uploaded successfully.")
            else:
                messagebox.showerror("Failed", response.json().get("error", "Unknown error."))
        except Exception as e:
            messagebox.showerror("Error", f"Could not upload puzzle: {e}")
            
        root.event_generate("<<CANCEL>>")  #return to menu

    EditorView(root, on_submit)

#game start
def _start_game(root, username, puzzle_id):
    """
    Called by MenuView or other functions when a puzzle needs to be launched.
    Loads the puzzle data and creates a PuzzleView.
    """
    puzzle = get_puzzle(puzzle_id)
    if puzzle:
        PuzzleView(root, username, puzzle)
    else:
        messagebox.showerror("Error", f"Could not load puzzle ID {puzzle_id}")

def _open_nyt_puzzle(root, username):
    """
    Download the latest puzzle, save it to the DB, and launch it in the game UI.
    """
    try:
        # Download and save the puzzle
        result = download_and_save_puzzle()
        messagebox.showinfo("NYT Puzzle", f"Downloaded puzzle: {result}")

        # Fetch the most recent puzzle from the DB
        puzzle_id = get_last_inserted_puzzle_id()
        if puzzle_id is not None:
            _start_game(root, username, puzzle_id)
        else:
            messagebox.showerror("Error", "No puzzle was saved.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load NYT puzzle:\n{e}")
    
def _quick_create(root):
    """Create a simple puzzle in one step."""
    def on_submit(puzzle_data):
        try:
            response = requests.post(
                SERVER_URL + ADD_PUZZLE,
                json={
                    "name": puzzle_data["name"],
                    "grid": puzzle_data["grid"],
                    "clues_across": puzzle_data["clues_across"],
                    "clues_down": puzzle_data["clues_down"],
                    "answers": puzzle_data["answers"]
                }
            )
            
            if response.status_code == 201:
                messagebox.showinfo("Success", "Puzzle uploaded successfully.")
            else:
                messagebox.showerror("Failed", response.json().get("error", "Unknown error."))
        except Exception as e:
            messagebox.showerror("Error", f"Could not upload puzzle: {e}")
            
        root.event_generate("<<CANCEL>>")  # return to menu
    
    # Create the SimpleCreatorView with the on_submit callback
    from app.view.simple_creator_view import SimpleCreatorView
    SimpleCreatorView(root, on_submit)

def _show_activity_feed(root):
    """
    Show activity feed view
    """
    acts = rec_activity(limit=50)
    FeedView(root, acts)

# Social feature entry
def _enter_social(root, username):
    """
    Open social feature interface
    """
    from app.view.social_view import SocialView
    SocialView(root, username, socketio=sio)

#function to increment puzzles solved; called from PuzzleView
def increment_puzzles_solved():
    """Increment the counter for completed puzzles"""
    global _puzzles_solved
    _puzzles_solved += 1
    return _puzzles_solved


def get_puzzles_solved():
    """Get the number of completed puzzles"""
    return _puzzles_solved