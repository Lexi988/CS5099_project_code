# app/view/base_view.py
import tkinter as tk
from typing import Protocol

"""Code refactored/ modulatised from /legacy/client.py
to /app/view/base_view.py
"""

class Clearable(Protocol):
    def winfo_children(self): ...
    def title(self, *_): ...

class BaseView:

    def _clear(self, root: Clearable, *, title: str | None = None) -> None:
        for w in root.winfo_children():
            w.destroy()
        if title:
            root.title(title)
