import os
import requests
import puz
import sqlite3
from app.config import DB_FILE, BASE_DIR
import json

def download_puzzle(url=None, output_file=None):
    """Download a puzzle from a given URL"""
    if url is None:
        # List of URLs to try in order
        urls = [
            "http://herbach.dnsalias.com/uc/uc231221.puz",
            "http://herbach.dnsalias.com/uc/uc231220.puz",
            "http://herbach.dnsalias.com/uc/uc231219.puz",
            "http://herbach.dnsalias.com/uc/uc231218.puz"
        ]
    else:
        urls = [url]
    
    if output_file is None:
        output_file = os.path.join(BASE_DIR, "daily.puz")
    
    # Try each URL in order
    for current_url in urls:
        try:
            print(f"Attempting to download puzzle from {current_url}")
            response = requests.get(current_url)
            
            if response.status_code != 200:
                print(f"Failed to download from {current_url}: HTTP {response.status_code}")
                continue
                
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            try:
                puzzle = puz.read(output_file)
                print(f"Successfully downloaded and parsed puzzle from {current_url}")
                return puzzle
            except Exception as e:
                print(f"Failed to parse puzzle from {current_url}: {e}")
                continue
                
        except Exception as e:
            print(f"Error downloading from {current_url}: {e}")
    
    # If we get here, all URLs failed
    raise Exception("Failed to download a valid puzzle from any of the available URLs")

def print_puzzle_info(puzzle):
    """Print information about a puzzle to console"""
    print("📘 Title:", puzzle.title)
    print("✍️ Author:", puzzle.author)
    print("🧠 First 5 clues:")
    for clue in puzzle.clues[:5]:
        print("  -", clue)
    
    return puzzle

def save_puzzle_to_db(puzzle):
    """Save a puzzle to the database"""
    try:
        title = puzzle.title
        author = puzzle.author
        
        print(f"Processing puzzle: {title} by {author}")
        print(f"Grid dimensions: {puzzle.width}x{puzzle.height}")
        
        # Get puzzle grid
        height, width = puzzle.height, puzzle.width
        grid = []
        
        # Check if solution is already a string or needs decoding
        print(f"Solution type: {type(puzzle.solution)}")
        if isinstance(puzzle.solution, bytes):
            solution = puzzle.solution.decode('utf-8')
        else:
            solution = str(puzzle.solution)  # Ensure it's a string
        
        print(f"First 10 chars of solution: {solution[:10]}")
        
        # Create grid as 2D array with empty or letter cells
        idx = 0
        for i in range(height):
            row = []
            for j in range(width):
                if idx < len(solution):
                    cell = solution[idx] if solution[idx] != '.' else ""
                    row.append(cell)
                    idx += 1
                else:
                    row.append("")  # Handle case where solution is too short
            grid.append(row)
        
        # Process clues
        clues_across = {}
        clues_down = {}
        
        # Get numbering for clues
        numbering = puzzle.clue_numbering()
        
        print(f"Number of across clues: {len(numbering.across)}")
        print(f"Number of down clues: {len(numbering.down)}")
        
        # Extract across clues
        for clue in numbering.across:
            number = clue['num']
            clue_idx = clue['clue_index']
            if clue_idx < len(puzzle.clues):
                clues_across[str(number)] = puzzle.clues[clue_idx]
        
        # Extract down clues
        for clue in numbering.down:
            number = clue['num']
            clue_idx = clue['clue_index']
            if clue_idx < len(puzzle.clues):
                clues_down[str(number)] = puzzle.clues[clue_idx]
        
        # Create answers dict
        answers = {}
        for i in range(height):
            for j in range(width):
                if i < len(grid) and j < len(grid[i]) and grid[i][j] != "":
                    answers[f"({i},{j})"] = grid[i][j]
        
        print(f"Processed {len(answers)} answer cells")
        
        # Save to database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO puzzles (name, grid, clues_across, clues_down, answers)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title, 
            json.dumps(grid),
            json.dumps(clues_across),
            json.dumps(clues_down),
            json.dumps(answers)
        ))
        conn.commit()
        conn.close()

        return f"✅ Downloaded and saved: {title} by {author} ({len(puzzle.clues)} clues)"
    except Exception as e:
        print(f"Error in save_puzzle_to_db: {e}")
        import traceback
        traceback.print_exc()
        raise

def download_and_save_puzzle(url=None, output_file=None):
    """Download a puzzle and save it to the database"""
    puzzle = download_puzzle(url, output_file)
    return save_puzzle_to_db(puzzle)