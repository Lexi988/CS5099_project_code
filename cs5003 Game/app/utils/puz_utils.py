import requests
import puz

# URL of a sample free puzzle in PUZ format
url = "http://herbach.dnsalias.com/uc/uc230505.puz"
filename = "daily.puz"

# Download the file
response = requests.get(url)
with open(filename, "wb") as f:
    f.write(response.content)
print("✅ Puzzle downloaded!")

# Load the file with puzpy
puzzle = puz.read(filename)
print("📘 Title:", puzzle.title)
print("✍️ Author:", puzzle.author)
print("🧠 First 5 clues:")
for clue in puzzle.clues[:5]:
    print(clue)