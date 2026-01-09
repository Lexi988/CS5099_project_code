# p3_cs5003_g4
# Crossword Puzzle Game
project 3 cs5003 MSc programming projects - group 4

## Project Structure

This project follows MVC (Model-View-Controller) architecture:

- **Model**: Database interactions in `app/model/db.py`
- **View**: UI components in `app/view/`
- **Controller**: Application logic in `app/controller/`

## Setup

### Prerequisites
- Python 3.8 or higher
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd p3_cs5003_g4
   ```

2. **Create/Activate Virtual Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate on macOS/Linux:
   source venv/bin/activate
   
   # Activate on Windows:
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Server
```bash
python main.py server
```
The server will start on `http://localhost:5001`

### Client
```bash
python main.py
```

## Features

- User authentication (login/registration)
- Play crossword puzzles
- Create puzzles (quick or advanced mode)
- View puzzle statistics
- Multiplayer game

## Testing

```bash
pytest app/tests/
```

## Project Contributors

- 230032580
- 240002187
- 240029852
- 240019931