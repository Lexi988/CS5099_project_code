# app/view/login_view.py

import tkinter as tk
from tkinter import messagebox
import requests
from app.shared.protocols import LOGIN_ENDPOINT, REGISTER_ENDPOINT
from app.config import SERVER_URL

#  Login / registration screen.
# MVC - view
#
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


import tkinter as tk
from tkinter import messagebox
import requests                       # HTTP client

#helper for self._clear()
from .base_view import BaseView

from app.shared.protocols import LOGIN_ENDPOINT, REGISTER_ENDPOINT
from app.config import SERVER_URL


class LoginView(BaseView):
    """
    Display login & registration UI
    """

    def __init__(self, root, on_success):
        """
        Init. login view.

        """
        self.root       = root
        self.on_success = on_success
        self._build_ui()

    
    # ui const. helpers - refactored / moved from /legacy code (client.py)
    def _build_ui(self):
        """
        Construct the login UI with username/password fields and buttons.
        """
        #DEBUG: replaced the old loop over winfo_children():
        self._clear(self.root, title="Crossword Login")
        
        # Add the course and student ID info
        tk.Label(self.root, text="CS5003 P3", font=("Helvetica", 14)).pack(pady=10)
        tk.Label(self.root, text="230032580,240002187,240029852,240019931,230032800").pack(pady=5)
        
        # Original login form
        tk.Label(self.root, text="Login", font=("Helvetica", 16)).pack(pady=10)
        tk.Label(self.root, text="Username:").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()
        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Login",
                command=self._attempt_login).pack(pady=5)
        tk.Button(self.root, text="Register",
                command=self._attempt_register).pack(pady=5)


    # network / validation actions
    def _attempt_login(self):
        """
        Val login credentials and send to server
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error",
                                "Please enter both username and password.")
            return

        try:
            print(f"Attempting login with {username}")
            
            resp = requests.post(
                SERVER_URL + LOGIN_ENDPOINT,
                json={"username": username, "password": password},
                timeout=5
            )
            
            print(f"Response status: {resp.status_code}")
            print(f"Response content: {resp.text}")
            
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print(f"Parsed JSON: {data}")
                except ValueError:
                    print("Could not parse JSON response")
                    
                # This is the important part that calls the success callback
                self.on_success(self.root, username)
            else:
                # safe JSON parse fallback
                try:
                    err = resp.json().get("message", "Login failed.")
                except ValueError:
                    err = resp.text or "Login failed (no details)."
                messagebox.showerror("Login Failed", err)
                
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Could not reach server:\n{e}")
            return





    def _attempt_register(self):
        """
        Reg, new user 
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error",
                                 "Please enter both username and password.")
            return

        try:
            resp = requests.post(
                SERVER_URL + REGISTER_ENDPOINT,
                json={"username": username, "password": password},
                timeout=5
            )
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Could not reach server:\n{e}")
            return

        if resp.status_code == 201:
            messagebox.showinfo("Success",
                                "Registered successfully.\nPlease log in.")
        else:
            try:
                err = resp.json().get("message", "Registration failed.")
            except ValueError:
                err = resp.text or "Registration failed (no details)."
            messagebox.showerror("Register Failed", err)
