from app.utils.puzzle_downloader import download_puzzle, print_puzzle_info
 
# Run the download and print info
puzzle = download_puzzle()
print("✅ Puzzle downloaded!")
print_puzzle_info(puzzle)