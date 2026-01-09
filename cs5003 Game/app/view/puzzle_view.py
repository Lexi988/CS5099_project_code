#app/view/puzzle_view.py

"""puzzle grid, timer, submit/share"""

import tkinter as tk
from tkinter import messagebox
import time
import requests
import pyperclip

from app.config import SERVER_URL
from app.shared.protocols import SUBMIT_RESULT_ENDPOINT
from app.model.db import rate_puzzle, get_puzzle_ratings


class PuzzleView:
    """
    displays a crossword puzzle, handles timer, submissions, and sharing.
    """

    def __init__(self, root, username, puzzle):
        self.root     = root
        self.username = username
        self.puzzle   = puzzle
        self.entries  = {}
        self.start_time = time.time()
        self.total_time = 5 * 60  # 5 min
        self._build_ui()

    def _build_ui(self):
        #xlear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.title(f"Puzzle: {self.puzzle['name']}")

        #puzzle title
        tk.Label(
            self.root,
            text=f"Puzzle: {self.puzzle['name']}",
            font=("Helvetica", 14)
        ).pack(pady=10)

        #grid
        grid_frame = tk.Frame(self.root)
        grid_frame.pack()
        for i, row in enumerate(self.puzzle["grid"]):
            for j, cell in enumerate(row):
                if cell != "":
                    entry = tk.Entry(grid_frame, width=2, font=("Courier",18), justify="center")
                    entry.grid(row=i, column=j)
                    self.entries[(i,j)] = entry
                else:
                    tk.Label(grid_frame, width=2, text=" ", bg="lightgray")\
                      .grid(row=i, column=j)

        #back button (only keep this one outside info panel for easy navigation)
        tk.Button(self.root, text="Back", command=self._go_back).pack(pady=5, side=tk.BOTTOM)

        # Build info panel
        self._build_info_panel()
        
        # Start timer
        self._update_timer()

    def _build_info_panel(self):
        """Builds an info panel with puzzle details, timer, and action buttons."""
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(pady=10)

        # Puzzle details
        tk.Label(self.info_frame, text=f"Puzzle: {self.puzzle['name']}",
                 font=("Helvetica", 12)).pack()

        # Timer
        self.timer_label = tk.Label(self.info_frame, text="Time Left: 05:00",
                                    font=("Helvetica", 12), fg="blue")
        self.timer_label.pack()

        #action buttons
        tk.Button(self.info_frame, text="Submit", command=self._submit_answers).pack(pady=5)
        self.share_button = tk.Button(
            self.info_frame,
            text="Share Result",
            command=self._share_results,
            state=tk.DISABLED
        )
        self.share_button.pack(pady=5)
        tk.Button(self.info_frame, text="Show Clues", command=self._show_clues).pack(pady=5)

        #button to view ratings
        tk.Button(self.info_frame, text="View Ratings",
                  command=self._show_ratings_view).pack(pady=5)
        
        #button to rate puzzle
        tk.Button(self.info_frame, text="Rate Game",
                command=self._show_rating_dialog).pack(pady=5)

    def _update_timer(self):
        elapsed   = int(time.time() - self.start_time)
        remaining = max(0, self.total_time - elapsed)
        mins, secs = divmod(remaining, 60)
        
        # Make sure timer_label has been created
        if hasattr(self, 'timer_label'):
            self.timer_label.config(text=f"Time Left: {mins:02}:{secs:02}")
            
        if remaining > 0:
            self.timer_job = self.root.after(1000, self._update_timer)
        else:
            messagebox.showwarning("Time's Up", "You ran out of time!")
            self._submit_answers(timeout=True)

    def _submit_answers(self, timeout=False):
        #stop timer if still running
        if hasattr(self, 'timer_job'):
            self.root.after_cancel(self.timer_job)

        correct = 0
        total   = len(self.puzzle["answers"])
        for key, value in self.puzzle["answers"].items():
            # convert string to tuple
            pos   = tuple(map(int, key.strip("()").split(",")))
            guess = self.entries[pos].get().upper()
            if guess == value:
                correct += 1
                self.entries[pos].config(bg="lightgreen")
            else:
                self.entries[pos].config(bg="lightcoral")

        elapsed = int(time.time() - self.start_time)
        
        #submit result to server
        try:
            requests.post(
                f"{SERVER_URL}{SUBMIT_RESULT_ENDPOINT}",
                json={
                    "username":   self.username,
                    "puzzle_id":  self.puzzle["id"],
                    "score":      correct,
                    "time":       elapsed
                },
                timeout=5
            )
        except Exception as e:
            print(f"Issue sending result: {e}")

        messagebox.showinfo(
            "Result",
            f"Score: {correct}/{total} in {elapsed//60}m {elapsed%60}s"
        )
        
        # Make sure share_button has been created
        if hasattr(self, 'share_button'):
            self.share_button.config(state=tk.NORMAL)
        
        #rating
        self.root.after(1000, self._show_rating_dialog)

    def _show_clues(self):
        clue_text = "Across:\n" + "\n".join(self.puzzle["clues_across"].values())
        clue_text += "\n\nDown:\n" + "\n".join(self.puzzle["clues_down"].values())
        messagebox.showinfo("Clues", clue_text)

    def _share_results(self):
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        correct = sum(1 for pos, entry in self.entries.items() 
                    if entry.get().upper() == self.puzzle["answers"][f"({pos[0]},{pos[1]})"])
        total = len(self.puzzle["answers"])
        
        msg = (f"{self.username} just completed the puzzle '{self.puzzle['name']}' "
            f"in {mins}m {secs}s with a score of {correct}/{total}! 🎉 "
            "#CrosswordChallenge")
        pyperclip.copy(msg)
        messagebox.showinfo("Shared!", "Result copied to clipboard!\nPaste it into your social app.")

    def _go_back(self):
        #return to main menu
        from app.controller.client_controller import _on_login
        _on_login(self.root, self.username)



    #rating dialog - community stats/ratings
    def _show_rating_dialog(self):
        """Show rating dialog for the puzzle"""
        from tkinter import Toplevel, Label, Text, Button, IntVar, Radiobutton
        import tkinter as tk
        
        rating_dialog = Toplevel(self.root)
        rating_dialog.title("Rate This Puzzle")
        rating_dialog.geometry("500x400")
        rating_dialog.configure(bg="#333333")
        rating_dialog.resizable(False, False)
        #dialog modal - prevents interacting with main window until closed

        rating_dialog.transient(self.root)  
        rating_dialog.grab_set()
        rating_dialog.focus_set()
      
        # Center the dialog
        rating_dialog.update_idletasks()
        x = (rating_dialog.winfo_screenwidth() - rating_dialog.winfo_width()) // 2
        y = (rating_dialog.winfo_screenheight() - rating_dialog.winfo_height()) // 2
        rating_dialog.geometry(f"+{x}+{y}")
        
        # Title
        Label(rating_dialog, text="How would you rate this puzzle?", 
              font=("Arial", 16), bg="#333333", fg="white").pack(pady=20)
        
        # Rating selection
        rating_var = IntVar(value=5)  # 5 star
        
        # Radio buttons with star labels
        for i in range(1, 6):
            stars = "★" * i + "☆" * (5-i)
            rb = Radiobutton(
                rating_dialog, 
                text=stars, 
                variable=rating_var, 
                value=i,
                font=("Arial", 14),
                bg="#333333", 
                fg="white",
                selectcolor="#333333",
                activebackground="#333333"
            )
            rb.pack(anchor="center", pady=5)
        
        #comment section
        Label(rating_dialog, text="Comment (optional):", 
              font=("Arial", 14), bg="#333333", fg="white").pack(pady=(20, 5), anchor="w", padx=20)
        
        comment_text = Text(rating_dialog, height=5, width=50, bg="#222222", fg="white")
        comment_text.pack(pady=5, padx=20)
        
        # Define submit function here; has access to the dialog widgets
        def submit_rating():
            try:
                rating = rating_var.get()
                comment = comment_text.get("1.0", tk.END).strip()
                from app.model.db import rate_puzzle
                success = rate_puzzle(self.puzzle["id"], self.username, rating, comment)
                if success:
                    messagebox.showinfo("Thank You", "Your rating has been submitted!")
                    rating_dialog.destroy()
                else:
                    messagebox.showerror("Error", "Failed to submit rating. Please try again.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        #create button for submmitting
        submit_btn = tk.Button(
            rating_dialog,
            text="SUBMIT RATING",
            command=submit_rating,
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10
        )
        submit_btn.pack(pady=20)
        
        rating_dialog.bind("<Return>", lambda event: submit_rating())


    def _show_ratings_view(self):
        """Show a window with all ratings for this puzzle."""
        ratings_window = tk.Toplevel(self.root)
        ratings_window.title(f"Ratings for {self.puzzle['name']}")
        ratings_window.geometry("500x400")
        
        ratings_data = get_puzzle_ratings(self.puzzle["id"])
        avg = ratings_data["average"]
        count = ratings_data["count"]
        ratings = ratings_data["ratings"]
        
        #header
        tk.Label(ratings_window, 
                 text=f"Ratings for {self.puzzle['name']}",
                 font=("Helvetica", 14, "bold")).pack(pady=10)
        
        tk.Label(ratings_window,
                 text=f"Average Rating: {avg:.1f}/5 ({count} ratings)",
                 font=("Helvetica", 12)).pack(pady=5)
        
        #ratings list with scrollbar
        frame = tk.Frame(ratings_window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill='both', expand=True)
        
        scrollbar.config(command=canvas.yview)
        
        ratings_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=ratings_frame, anchor='nw')
        
        #display ratings
        for i, (username, rating, comment, timestamp) in enumerate(ratings):
            review_frame = tk.Frame(ratings_frame, bd=1, relief=tk.SOLID)
            review_frame.pack(fill='x', padx=5, pady=5, expand=True)
            
            header_frame = tk.Frame(review_frame)
            header_frame.pack(fill='x', expand=True, padx=5, pady=3)
            
            tk.Label(header_frame, 
                     text=f"{username}",
                     font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
                     
            tk.Label(header_frame,
                     text=f"{'★' * rating}{'☆' * (5-rating)}",
                     font=("Helvetica", 10)).pack(side=tk.LEFT, padx=10)
                     
            tk.Label(header_frame,
                     text=timestamp,
                     font=("Helvetica", 8),
                     fg="gray").pack(side=tk.RIGHT)
            
            if comment:
                tk.Label(review_frame,
                         text=comment,
                         wraplength=450,
                         justify=tk.LEFT).pack(fill='x', padx=5, pady=3)
        
        #update scroll region
        ratings_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        tk.Button(ratings_window, text="Close", 
                  command=ratings_window.destroy).pack(pady=10)