# app/view/menu_view.py

"""
# Main menu screen shown after a successful login.
# This class is responsible for displaying the main menu, including
# the welcome message, buttons for different actions, and a list of
# active multiplayer games."""

#libs
import tkinter as tk
from tkinter import ttk, messagebox
from app.model.db import get_friend_activities, format_activity_message
from app.utils.puzzle_downloader import download_and_save_puzzle


# Add this method in MenuView:
def _handle_download(self):
    result = download_and_save_puzzle()
    messagebox.showinfo("Puzzle Downloaded", result)


# REFERENCE:
#   nested-frames logic (group buttons) adapted/taken from:
#   https://www.pythonguis.com/tutorials/use-tkinter-to-design-gui-layout/

# hierarchy, children adapted from  https://tkdocs.com/tutorial/concepts.html
# windows and dialogs code adapted from: https://tkdocs.com/tutorial/windows.html

class MenuView:
    """
    main-menu screen shown after a successful login
    """

    def __init__(
        self,
        root,
        username,
        play_callback,          #play-puzzle
        stats_callback,         #stats
        add_callback,           #adv. editor
        quit_callback,          #quit app
        nyt_callback,           #daily puzzle import 
        quick_callback,         #quick-create/simple editor
        active_games            #list of active games; tuple
    ):
        self.root           = root
        self.username       = username
        self.play_callback  = play_callback
        self.stats_callback = stats_callback
        self.add_callback   = add_callback
        self.quit_callback  = quit_callback
        self.nyt_callback   = nyt_callback
        self.quick_callback = quick_callback
        self.active_games   = active_games

        #child can raise cancel to rebuild menu
        self.root.bind("<<CANCEL>>", lambda e: self._build_main_menu())

        self._build_main_menu()

    #  MAIN MENU LAYOUT
    # REF:
    # nested frames logic adapted from:
    #  https://www.pythonguis.com/tutorials/use-tkinter-to-design-gui-layout/

    def _build_main_menu(self):
        """Welcome → button-bar → active-games listbox"""
        self._clear()
        self.root.title("Crossword Main Menu")

        #heading
        tk.Label(
            self.root,
            text=f"Welcome, {self.username}",
            font=("Helvetica", 16)
        ).pack(pady=(10, 6))

        # button bar    (all buttons inside one frame)
        btn_bar = tk.Frame(self.root)
        btn_bar.pack(pady=4)

        for text, cmd in [
            ("Play Puzzle",              self.play_callback),
            ("NYT Daily Puzzle",         self.nyt_callback),
            ("Create Puzzle – Quick",    self.quick_callback),
            ("Create Puzzle – Advanced", self.add_callback),
            ("Download Puzzle",          self._handle_download),
            ("My Stats",                 lambda: self._enter_stats()),
            ("Social",                   lambda: self._enter_social()),
            ("Quit",                     self.quit_callback),
        ]:
            tk.Button(btn_bar, text=text, width=24, command=cmd) \
                .pack(pady=2, fill="x")

        #active games list (stretches with window)
        tk.Label(
            self.root, text="Active Multiplayer Games",
            font=("Helvetica", 12, "bold")
        ).pack(pady=(8, 4))

        list_frame = tk.Frame(self.root)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        games_lb = tk.Listbox(list_frame, width=46)
        games_lb.grid(row=0, column=0, sticky="nsew")

        if not self.active_games:
            games_lb.insert(tk.END, "No games found")
        else:
            for gid, name, players in self.active_games:
                games_lb.insert(tk.END, f"{gid} – {name} ({players} players)")

    def _enter_puzzle_list(self):
        """get puzzles and show the list screen."""
        puzzles = self.play_callback()
        self._show_puzzles(puzzles, start_callback=self._start_game)

    def _show_puzzles(self, puzzles, start_callback):
        """display listbox of puzzles + back button."""
        for w in self.root.winfo_children():
            w.destroy()

        tk.Label(self.root,
                 text="Select a Puzzle",
                 font=("Helvetica", 14)).pack(pady=10)

        # Create frame for listbox and scrollbar
        list_frame = tk.Frame(self.root)
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create listbox with scrollbar
        listbox = tk.Listbox(list_frame, width=40, height=10, yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for pid, name in puzzles:
            listbox.insert(tk.END, f"{pid}: {name}")

        # Button frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        def on_select():
            sel = listbox.curselection()
            if not sel:
                return
            puzzle_id = puzzles[sel[0]][0]
            start_callback(puzzle_id)

        tk.Button(btn_frame, text="Play Selected",
                  command=on_select).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Back to Menu",
                  command=self._build_main_menu).pack(side=tk.LEFT, padx=5)

    def _start_game(self, puzzle_id):
        """hand off to controller to launch PuzzleView."""
        from app.model.db import get_puzzle
        from app.view.puzzle_view import PuzzleView
        
        puzzle = get_puzzle(puzzle_id)
        if puzzle:
            PuzzleView(self.root, self.username, puzzle)
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Could not load puzzle ID {puzzle_id}")

    def _enter_stats(self):
        """get stats and show the stats screen with tabs"""
        stats = self.stats_callback()
        activities = get_friend_activities(self.username)
        self._show_stats_and_activities(stats, activities)

    def _show_stats_and_activities(self, stats, activities):
        """display tabbed view with stats and friend activities"""
        for w in self.root.winfo_children():
            w.destroy()
            
        self.root.title("Stats & Activity")
            
        # Create a tab control
        tab_control = ttk.Notebook(self.root)
        
        # Create the tabs
        stats_tab = ttk.Frame(tab_control)
        activity_tab = ttk.Frame(tab_control)
        
        tab_control.add(stats_tab, text='My Stats')
        tab_control.add(activity_tab, text='Friend Activity')
        
        tab_control.pack(expand=1, fill="both", padx=10, pady=10)
        
        # Populate My Stats tab
        self._populate_stats_tab(stats_tab, stats)
        
        # Populate Friend Activity tab
        self._populate_activity_tab(activity_tab, activities)
        
        # Back button
        tk.Button(self.root,
                  text="Back to Menu",
                  command=self._build_main_menu).pack(pady=10)

    def _populate_stats_tab(self, parent, stats):
        """Populate the stats tab with user statistics"""
        tk.Label(parent,
                 text="Your Puzzle Statistics",
                 font=("Helvetica", 14)).pack(pady=10)

        if not stats:
            tk.Label(parent,
                     text="You haven't completed any puzzles yet.").pack(pady=10)
        else:
            frame = tk.Frame(parent)
            frame.pack(padx=10, pady=10, fill='both', expand=True)

            # Table headers
            for col, h in enumerate(("Puzzle","Score","Time","Date")):
                tk.Label(frame,
                         text=h,
                         font=("Helvetica", 10, "bold")).grid(row=0, column=col, padx=5, sticky='w')

            # Table rows
            for i, (name, score, t_taken, ts) in enumerate(stats, start=1):
                tk.Label(frame, text=name).grid(row=i, column=0, padx=5, sticky='w')
                tk.Label(frame, text=score).grid(row=i, column=1, padx=5)
                tk.Label(frame, text=f"{t_taken}s").grid(row=i, column=2, padx=5)
                tk.Label(frame, text=ts).grid(row=i, column=3, padx=5)

    def _populate_activity_tab(self, parent, activities):
        """Populate the activity tab with friend activities"""
        tk.Label(parent,
                 text="Recent Friend Activity",
                 font=("Helvetica", 14)).pack(pady=10)

        if not activities:
            tk.Label(parent,
                     text="No friend activity to display. Add friends to see their activities here!").pack(pady=10)
        else:
            # Create a frame with scrollbar for activities
            frame_outer = tk.Frame(parent)
            frame_outer.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Add a scrollbar
            scrollbar = tk.Scrollbar(frame_outer)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Create a canvas for scrolling
            canvas = tk.Canvas(frame_outer, yscrollcommand=scrollbar.set)
            canvas.pack(side=tk.LEFT, fill='both', expand=True)
            
            # Configure the scrollbar
            scrollbar.config(command=canvas.yview)
            
            # Create a frame inside the canvas
            activity_frame = tk.Frame(canvas)
            canvas.create_window((0, 0), window=activity_frame, anchor='nw')
            
            # Populate with activities
            for i, activity in enumerate(activities):
                message = format_activity_message(activity)
                timestamp = activity["timestamp"]
                
                act_frame = tk.Frame(activity_frame, bd=1, relief=tk.SOLID)
                act_frame.pack(fill='x', padx=5, pady=5)
                
                tk.Label(act_frame, 
                         text=message,
                         justify=tk.LEFT,
                         anchor='w',
                         wraplength=400).pack(side=tk.TOP, fill='x', padx=5, pady=2)
                         
                tk.Label(act_frame,
                         text=timestamp,
                         font=("Helvetica", 8),
                         fg="gray").pack(side=tk.BOTTOM, fill='x', padx=5, pady=2)
            
            # Update the canvas scroll region
            activity_frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

    def _enter_social(self):
        """Enter social features interface"""
        from app.controller.client_controller import _enter_social
        _enter_social(self.root, self.username)

    #helper function to clear the root window
    # before building a new screen
    def _clear(self):
        """Remove every widget from root."""
        for w in self.root.winfo_children():
            w.destroy()

    # STATIC utils. (called by controller)
    @staticmethod
    def clear_and_show_puzzles(root, puzzles, start_callback, delete_callback=None):
        """Replace the root window with a list-of-puzzles screen."""
        for w in root.winfo_children():
            w.destroy()

        tk.Label(root, text="Select a Puzzle",
                 font=("Helvetica", 14)).pack(pady=10)

        # Create a frame for the listbox and scrollbar
        list_frame = tk.Frame(root)
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create listbox with scrollbar
        lb = tk.Listbox(list_frame, width=40, height=10, yscrollcommand=scrollbar.set)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=lb.yview)
        
        # Populate listbox
        for pid, name in puzzles:
            lb.insert(tk.END, f"{pid}: {name}")

        # Button frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        def _on_select():
            sel = lb.curselection()
            if sel:
                start_callback(puzzles[sel[0]][0])
                
        def _on_delete():
            sel = lb.curselection()
            if sel:
                delete_callback(puzzles[sel[0]][0])

        # Add buttons to button frame
        tk.Button(btn_frame, text="Play Selected",
                  command=_on_select).pack(side=tk.LEFT, padx=5)
                  
        # Only show delete button if callback is provided
        if delete_callback:
            tk.Button(btn_frame, text="Delete Selected",
                    command=_on_delete).pack(side=tk.LEFT, padx=5)
                  
        tk.Button(btn_frame, text="Back to Menu",
                  command=lambda: root.event_generate("<<CANCEL>>")
                  ).pack(side=tk.LEFT, padx=5)

    @staticmethod
    def clear_and_show_stats(root, stats):
        """Replace the root window with a stats table."""
        for w in root.winfo_children():
            w.destroy()

        tk.Label(root, text="Your Puzzle Statistics",
                 font=("Helvetica", 14)).pack(pady=10)

        if not stats:
            tk.Label(root, text="No puzzles completed yet.") \
                .pack(pady=10)
        else:
            frame = tk.Frame(root)
            frame.pack(padx=10, pady=10, fill='both', expand=True)

            headers = ("Puzzle", "Score", "Time", "Date")
            for c, h in enumerate(headers):
                tk.Label(frame, text=h,
                         font=("Helvetica", 10, "bold")) \
                    .grid(row=0, column=c, padx=5, sticky='w')

            for r, (name, score, secs, ts) in enumerate(stats, 1):
                tk.Label(frame, text=name).grid(row=r, column=0, sticky='w')
                tk.Label(frame, text=score).grid(row=r, column=1)
                tk.Label(frame, text=f"{secs}s").grid(row=r, column=2)
                tk.Label(frame, text=ts).grid(row=r, column=3)

        tk.Button(root, text="Back to Menu",
                  command=lambda: root.event_generate("<<CANCEL>>")
                  ).pack(pady=10)

    def _handle_download(self):
        result = download_and_save_puzzle()
        messagebox.showinfo("Puzzle Downloaded", result)