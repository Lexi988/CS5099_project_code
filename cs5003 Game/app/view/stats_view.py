# app/view/stats_view.py
import tkinter as tk
from .base_view import BaseView

class StatsView(BaseView):
    """Simple read-only stats. screen.
    code refactored from legacy code.
    This class handles usr stats
    """

    def __init__(self, root, username: str, stats: dict[str, int], on_back):
        self.root      = root
        self.username  = username
        self.stats     = stats
        self.on_back   = on_back
        self._build_ui()

    def _build_ui(self):
        self._clear(self.root, title=f"{self.username} – Stats")

        tk.Label(self.root, text="Your statistics",
                font=("Helvetica", 16)).pack(pady=10)

        if not self.stats:
            tk.Label(self.root, text="The puzzle is not completed").pack(pady=10)
        else:
            # Format similar to legacy code
            formatted_stats = "\n".join(
                f"{name}: {score} correct in {time}s on {date}"
                for name, score, time, date in self.stats
            )
            tk.Label(self.root, text=formatted_stats, justify=tk.LEFT).pack(anchor="w", padx=20)

        tk.Button(self.root, text="Back", command=self.on_back).pack(pady=20)
