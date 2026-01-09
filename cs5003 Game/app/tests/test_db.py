import tempfile, os
from app.model import db
from app.controller.server_controller import create_app


def test_add_and_fetch_puzzle():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    db.DB_FILE = path     

    db.init_db()
    db.add_puzzle("Test", [["T"]], {}, {}, {"0,0":"T"})
    puzzles = db.get_puzzles()

    assert puzzles == [(1, "Test")]
