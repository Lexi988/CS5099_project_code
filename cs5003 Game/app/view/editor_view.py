#app/view/editor_view.py

"""“Add new puzzle dialogs"""
import tkinter as tk
from tkinter import simpledialog, messagebox

#REF:
#https://www.pythonguis.com/tutorials/use-tkinter-to-design-gui-layout/
#https://labex.io/tutorials/python-create-a-2048-game-with-python-tkinter-298860
# https://tkdocs.com/tutorial/windows.html
# https://tkdocs.com/tutorial/concepts.html


class EditorView:
    """
    Dialogs for creating and uploading new puzzle.
    """

    def __init__(self, root, on_submit):
        self.root      = root
        self.on_submit = on_submit
        self._build_ui()

    def _build_ui(self):
        #prompt for puzzle name
        name = simpledialog.askstring("Puzzle Name", "Enter puzzle name:", parent=self.root)
        if not name:
            return

        #prompt for grid size
        size = simpledialog.askinteger("Grid Size", "Enter grid size (e.g. 5):", parent=self.root)
        if not size:
            return

        grid    = []
        answers = {}

        #build the grid cell by cell
        for i in range(size):
            row = []
            for j in range(size):
                val = simpledialog.askstring(
                    "Grid Cell",
                    f"Letter at ({i},{j}) or leave blank:",
                    parent=self.root
                )
                if val:
                    val = val.strip().upper()
                    row.append(val)
                    answers[f"({i},{j})"] = val
                else:
                    row.append("")
            grid.append(row)

        #across clues
        clues_across = {}
        count_across = simpledialog.askinteger(
            "Clues Across",
            "How many Across clues?",
            parent=self.root
        ) or 0
        for _ in range(count_across):
            k = simpledialog.askstring("Clue Number", "Clue number (e.g. 1):", parent=self.root)
            v = simpledialog.askstring("Clue Text", f"Text for Across clue {k}:", parent=self.root)
            if k and v:
                clues_across[k.strip()] = v.strip()

        #down clues
        clues_down = {}
        count_down = simpledialog.askinteger(
            "Clues Down",
            "How many Down clues?",
            parent=self.root
        ) or 0
        for _ in range(count_down):
            k = simpledialog.askstring("Clue Number", "Clue number (e.g. 2):", parent=self.root)
            v = simpledialog.askstring("Clue Text", f"Text for Down clue {k}:", parent=self.root)
            if k and v:
                clues_down[k.strip()] = v.strip()

        #confirm submission
        if messagebox.askyesno("Submit Puzzle", f"Upload puzzle '{name}'?"):
            # pass data back to controller for HTTP POST
            self.on_submit(name, grid, clues_across, clues_down, answers)

            messagebox.showinfo("Saved", "Your puzzle is ready!")
            self.root.event_generate("<<CANCEL>>")   # jump back to MenuView
            return                                  
        else:
            messagebox.showinfo("Cancelled", "Puzzle creation cancelled.")

        #back button only visible in dialog
        tk.Button(self.root, text="Back",
                  command=lambda: self.root.event_generate("<<CANCEL>>")
                  ).pack(pady=5)
        
        
