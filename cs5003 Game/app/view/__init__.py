# app/view/__init__.py
from .login_view   import LoginView
from .menu_view    import MenuView
from .puzzle_view  import PuzzleView
from .editor_view  import EditorView
from .simple_creator_view import SimpleCreatorView
from .stats_view   import StatsView

__all__ = [n for n in dir() if n.endswith("View")]
