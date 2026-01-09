import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.utils.dictionary import Dictionary

# REF:
#  Tkinter:  https://docs.python.org/3/library/tkinter.html
#https://www.pythonguis.com/tutorials/use-tkinter-to-design-gui-layout/
#https://labex.io/tutorials/python-create-a-2048-game-with-python-tkinter-298860
# https://tkdocs.com/tutorial/windows.html
# https://tkdocs.com/tutorial/concepts.html

#Python Simplified, “Create GUI App with Tkinter and SQLite - 
# Step by Step Python Tutorial for Beginners,” YouTube. Jun. 15, 2022. 
# Accessed: Apr. 12, 2025. [Online]. Available:
# https://www.youtube.com/watch?v=5qOnzF7RsNA

# NeuralNine, “Tkinter Beginner Course - Python GUI Development,” 
# YouTube. Sep. 29, 2021. Accessed: Apr. 13, 2025. 
# [Online]. Available: https://www.youtube.com/watch?v=ibf5cx221hk 

#Python Tkinter GUI,” 
# www.youtube.com. https://www.youtube.com/watch?v=TuLxsvK4sv
#by https://www.youtube.com/@BroCodez



class SimpleCreatorView:
    """
    Quick-mode crossword creator:

    - User picks grid size: square, odd numbers up to 13x13; 
    - shows max char count so user can enter words
    - When full, grey-out entry box and enable Create button
    - pass a puzzle-dict to on_submit(puzzle) when created """

    def __init__(self, root, on_submit):
        self.root = root
        self.on_submit = on_submit
        self._chars_max = 0
        self.dictionary = Dictionary()  # Initialize dictionary here
        self._build_ui()


    def _validate_words(self, words):
        """validate words against dict and offer suggestions for invalid ones."""
        invalid_words = []
        suggestions = {}
        
        for word in words:
            if not self.dictionary.is_valid_word(word):
                invalid_words.append(word)
                # Get suggestions for invalid words
                word_suggestions = self.dictionary.suggest_words(word, limit=5)
                if word_suggestions:
                    suggestions[word] = word_suggestions
        
        if invalid_words:
            message = "The following words are not in the dictionary:\n"
            message += ", ".join(invalid_words)
            
            if suggestions:
                message += "\n\nSuggestions:"
                for word, word_suggs in suggestions.items():
                    message += f"\nFor '{word}': {', '.join(word_suggs)}"
            
            message += "\n\nWould you like to replace invalid words with suggestions?"
            
            if messagebox.askyesno("Invalid Words", message):
                # Replace words with suggestions
                self._replace_invalid_words(invalid_words, suggestions)
                return True
            
            # Ask if the user wants to continue without replacing
            return messagebox.askyesno("Continue Anyway?", 
                                      "Do you want to continue with invalid words?")
        
        return True
      
    def _create(self):
        size = self.size_var.get()
        words = self._get_words()
        
        #dict. validation
        if not self._validate_words(words):
            return  #user cancel for invalid words
        
        #choose based on radio button selection
        layout_type = self.layout_var.get()
        
        #try gen. both layouts
        try:
            if layout_type == "crossword":
                #gen. cw layout
                grid, clues_across, clues_down, answers = self._generate_crossword_layout(words)
                puzzle = {
                    "name": f"Crossword {size}×{size}",
                    "grid": grid,
                    "clues_across": clues_across,
                    "clues_down": clues_down,
                    "answers": answers,
                }
                self.on_submit(puzzle)  #pass puzz dict; already created
                
                #show success mesg; return to menu
                messagebox.showinfo("Saved", "Your crossword puzzle is ready!")
                self.root.event_generate("<<CANCEL>>")  #back to menu
            else:
                #simple layout: place words horizontally - fill each row before moving to next
                grid = [[""]*size for _ in range(size)]
                answers, clues_across = {}, {}
                r=c=0; clue_no=1
                for w in words:
                    if c+len(w) > size:       #wrap if exceeds row
                        r += 1; c = 0
                    if r >= size:
                        messagebox.showerror(
                            "Overflow",
                            "Words don't fit – please remove a few.")
                        return
                    for ch in w:
                        grid[r][c]       = ch
                        answers[f"{r},{c}"] = ch
                        c += 1
                    clues_across[clue_no] = f"(quick) {w}"
                    clue_no += 1
                    if c < size: c += 1    #one space gap

                puzzle = {
                    "name": f"Quick {size}×{size}",
                    "grid": grid,
                    "clues_across": clues_across,
                    "clues_down": {},      #quick mode skips down clues
                    "answers": answers,
                }
                self.on_submit(puzzle) #puzzle is handed back to controller

                #success msg & back to menu
                messagebox.showinfo("Saved", "Your puzzle is ready!")
                self.root.event_generate("<<CANCEL>>")   # back to MenuView
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate layout: {e}")

    def _show_layout_preview(self, simple_grid, cross_grid, simple_callback, cross_callback):
        """Show preview of both layouts and let user choose"""
        preview = tk.Toplevel(self.root)
        preview.title("Choose Layout")
        
        # Simple layout preview on left
        simple_frame = tk.LabelFrame(preview, text="Simple Layout")
        simple_frame.grid(row=0, column=0, padx=10, pady=10)
        self._draw_grid_preview(simple_frame, simple_grid)
        tk.Button(simple_frame, text="Choose Simple", command=lambda: [preview.destroy(), simple_callback()]).pack(pady=5)
        
        # Crossword layout preview on right
        cross_frame = tk.LabelFrame(preview, text="Crossword Layout")
        cross_frame.grid(row=0, column=1, padx=10, pady=10)
        self._draw_grid_preview(cross_frame, cross_grid)
        tk.Button(cross_frame, text="Choose Crossword", command=lambda: [preview.destroy(), cross_callback()]).pack(pady=5)
        
    def _draw_grid_preview(self, parent, grid):
        """Draw a preview of a grid"""
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                bg_color = "white" if cell else "black"
                tk.Label(parent, text=cell, width=2, bg=bg_color, relief="solid", borderwidth=1).grid(row=i, column=j)
                
    def _submit_puzzle(self, layout_type, grid, clues_across, clues_down, answers):
        """Submit puzzle with the selected layout"""
        size = self.size_var.get()
        puzzle = {
            "name": f"{layout_type.capitalize()} {size}×{size}",
            "grid": grid,
            "clues_across": clues_across,
            "clues_down": clues_down,
            "answers": answers,
        }
        self.on_submit(puzzle)
        messagebox.showinfo("Saved", f"Your {layout_type} puzzle is ready!")
        self.root.event_generate("<<CANCEL>>")   # back to MenuView
        

    #simple mode auto layout with words
    def _generate_crossword_layout(self, words):
        """Generate optimal crossword layout from words"""
        # Sort words by length (longest first for better intersection chances)
        words = sorted(words, key=len, reverse=True)

        # Get grid size
        size = self.size_var.get()
        grid = [["" for _ in range(size)] for _ in range(size)]
        clues_across = {}
        clues_down = {}
        answers = {}

        #place first word horizontally in middle row
        start_row = size // 2
        start_col = (size - len(words[0])) // 2
        for i, char in enumerate(words[0]):
            grid[start_row][start_col + i] = char
            answers[f"{start_row},{start_col + i}"] = char
        
        clues_across[1] = f"First word: {words[0]}"
        
        placed_words = [words[0]]
        clue_number = 2
        
        #try to place remaining words
        for word in words[1:]:
            placed = False
            
            #try to find intersections with placed words
            for placed_word in placed_words:
                for char_idx in range(len(word)):
                    char = word[char_idx]
                    
                    #search for this character in placed words
                    for r in range(size):
                        for c in range(size):
                            if grid[r][c] == char:
                                #try vertical placement (if char matches)
                                if self._can_place_vertically(grid, word, r, c, char_idx):
                                    self._place_word_vertically(grid, word, r, c, char_idx, answers)
                                    clues_down[clue_number] = f"Clue for {word}"
                                    clue_number += 1
                                    placed_words.append(word)
                                    placed = True
                                    break
                                #try horizontal placement
                                elif self._can_place_horizontally(grid, word, r, c, char_idx):
                                    self._place_word_horizontally(grid, word, r, c, char_idx, answers)
                                    clues_across[clue_number] = f"Clue for {word}"
                                    clue_number += 1
                                    placed_words.append(word)
                                    placed = True
                                    break
                        if placed:
                            break
                    if placed:
                        break
                if placed:
                    break

        return grid, clues_across, clues_down, answers

    #vertical placement
    def _can_place_vertically(self, grid, word, r, c, char_idx):
        """Check if word can be placed vertically"""
        size = len(grid)
        start_r = r - char_idx
        
        # Check bounds
        if start_r < 0 or start_r + len(word) > size:
            return False
            
        # Check for conflicts
        for i, char in enumerate(word):
            curr_r = start_r + i
            if grid[curr_r][c] != "" and grid[curr_r][c] != char:
                return False
                
        return True
            

    def _build_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.title("Quick Crossword Creator")

        #grid size drop-down
        tk.Label(self.root, text="Grid size").pack()
        self.size_var = tk.IntVar(value=5)
        sizes = [3,5,7,9,11,13]
        ttk.Combobox(self.root, textvariable=self.size_var,
                    values=sizes, width=5,
                    state="readonly").pack()
        self.size_var.trace_add("write", self._update_budget)

        # Layout selection
        layout_frame = tk.Frame(self.root)
        layout_frame.pack(pady=10)
        
        tk.Label(layout_frame, text="Layout Style:").pack(side=tk.LEFT)
        
        self.layout_var = tk.StringVar(value="simple")
        tk.Radiobutton(
            layout_frame, text="Simple Horizontal", 
            variable=self.layout_var, value="simple"
        ).pack(side=tk.LEFT)
        
        tk.Radiobutton(
            layout_frame, text="Crossword", 
            variable=self.layout_var, value="crossword"
        ).pack(side=tk.LEFT)

        #words input
        tk.Label(self.root, text="Words (one per line)").pack(pady=(6,0))
        self.text = tk.Text(self.root, width=30, height=8)
        self.text.pack()
        self.text.bind("<KeyRelease>", lambda e: self._update_budget())

        # live counter
        self.counter = tk.Label(self.root, text="0 / 25")
        self.counter.pack(pady=(4,6))

        # buttons
        self.btn_create = tk.Button(self.root, text="Create",
                                    state=tk.DISABLED,
                                    command=self._create)
        self.btn_create.pack(pady=3)
        tk.Button(self.root, text="Cancel",
                command=lambda: self.root.event_generate("<<CANCEL>>")
                ).pack()

        self._update_budget()


    def _update_budget(self, *_):
        size = self.size_var.get()
        self._chars_max = size * size
        words = self._get_words()
        used  = sum(len(w) for w in words)
        self.counter.config(text=f"{used} / {self._chars_max}")
        ok = (0 < used <= self._chars_max)
        self.btn_create.config(state=tk.NORMAL if ok else tk.DISABLED)
        # prevent overflow
        if used > self._chars_max:
            self.counter.config(fg="red")
        else:
            self.counter.config(fg="black")

    def _get_words(self):
        return [w.strip().upper()
                for w in self.text.get("1.0", tk.END).splitlines()
                if w.strip()]

    #horizontal placement
    def _can_place_horizontally(self, grid, word, r, c, char_idx):
        """check if word can be placed horizontally"""
        size = len(grid)
        start_c = c - char_idx
        
        #check bounds
        if start_c < 0 or start_c + len(word) > size:
            return False
            
        #check any conflicts
        for i, char in enumerate(word):
            curr_c = start_c + i
            if grid[r][curr_c] != "" and grid[r][curr_c] != char:
                return False
                
        return True
    
    def _place_word_vertically(self, grid, word, r, c, char_idx, answers):
        """Place word vertically on grid"""
        start_r = r - char_idx  # Fixed variable name
        for i, char in enumerate(word):
            curr_r = start_r + i  # Fixed reference
            grid[curr_r][c] = char
            answers[f"{curr_r},{c}"] = char

    def _place_word_horizontally(self, grid, word, r, c, char_idx, answers):
        """Place word horizontally on grid"""
        start_c = c - char_idx
        for i, char in enumerate(word):
            curr_c = start_c + i
            grid[r][curr_c] = char
            answers[f"{r},{curr_c}"] = char