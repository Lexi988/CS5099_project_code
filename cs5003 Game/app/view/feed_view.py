import tkinter as tk
#class to handle shpwing the activty feed for the user interface
class FeedView:
    """
    This will show the recent events in the scrolling list
    It will have username, description, timestamp
    """

    def __init__(self, root, activities):
        self.root = root #root window
        self.activities = activities #holds activites, will be used for loop
        self._build_feed()

    #this creates the user interface elements
    def _build_ui(self): 
        for w in self.root.winfo_children(): #returns the command 
            w.destroy() #clears screen to start fresh
        self.root.title("Recent Activity") #title for window

        #this creates th actual widget itself for the window
        tk.Label(
            self.root,
            text="Recent Activity",
            font=("Helvetica", 16)
        ).pack(pady=10)

        frame = tk.Frame(self.root)
        #add frame to window
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        #scrollbar 
        scrollbar = tk.Scrollbar(frame)
        #this sets the position
        scrollbar.pack(side='right', fill='y')

        #listbox for the widget
        listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set, #links the scrolling to the scrollbar
            width=60,
            height=20
        )
        #loops through the activities
        for user, desc, ts in self.activities:
            #add line at botton of listbox
            listbox.insert(tk.END, f"[{ts}] {user} {desc}")
        listbox.pack(side='left', fill='both', expand=True)

        #link scrollbar to listbox
        scrollbar.config(command=listbox.yview)

        #creates the menu when called
        from app.controller.client_controller import _on_login
        tk.Button( #botton for back to menu
            self.root,
            text="Back to Menu",
            command=lambda: _on_login(self.root, self.username)
        ).pack(pady=10)