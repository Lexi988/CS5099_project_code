"""Social Features View - Friend Management and Chat"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import datetime
import json
from app.config import SERVER_URL
from app.shared.protocols import (
    SEARCH_USERS_ENDPOINT, FRIEND_REQUEST_ENDPOINT, 
    ACCEPT_FRIEND_ENDPOINT, REJECT_FRIEND_ENDPOINT,
    FRIENDS_LIST_ENDPOINT,
    MESSAGES_ENDPOINT, SEND_MESSAGE_ENDPOINT,
    UNREAD_COUNT_ENDPOINT
)

class SocialView:
    """
    Social feature main interface, includes friend management and messaging
    """
    def __init__(self, root, username, socketio=None):
        self.root = root
        self.username = username
        self.socketio = socketio
        self.current_chat = None
        
        # Clear existing components
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self._build_ui()
        self._load_data()
        
        # If socketio is provided, set up event handling
        if socketio:
            self._setup_socket_events()
    
    def _build_ui(self):
        """Build user interface"""
        self.root.title(f"Social - {self.username}")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar - Friends list
        left_frame = ttk.LabelFrame(main_frame, text="My Friends")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Friends list
        self.friends_list = tk.Listbox(left_frame)
        self.friends_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.friends_list.bind('<<ListboxSelect>>', self._on_friend_select)
        
        # Friend action buttons
        friend_btn_frame = ttk.Frame(left_frame)
        friend_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(friend_btn_frame, text="Add Friend", command=self._add_friend).pack(side=tk.LEFT, padx=2)
        ttk.Button(friend_btn_frame, text="Friend Requests", command=self._show_friend_requests).pack(side=tk.LEFT, padx=2)
        
        # Right sidebar - Chat area
        right_frame = ttk.LabelFrame(main_frame, text="Chat")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message area
        self.chat_area = tk.Text(right_frame, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message input area
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.msg_entry = ttk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.msg_entry.bind('<Return>', self._send_message)
        
        self.send_btn = ttk.Button(input_frame, text="Send", command=self._send_message)
        self.send_btn.pack(side=tk.RIGHT, padx=2)
        
        # Bottom navigation
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(nav_frame, text="Back to Menu", command=self._back_to_menu).pack(side=tk.LEFT, padx=5)
    
    def _load_data(self):
        """Load friend data"""
        try:
            response = requests.get(
                f"{SERVER_URL}{FRIENDS_LIST_ENDPOINT}",
                params={"username": self.username}
            )
            if response.status_code == 200:
                data = response.json()
                
                # Update friends list
                self.friends_list.delete(0, tk.END)
                for friend in data["friends"]:
                    self.friends_list.insert(tk.END, friend)
                
                # Check for unread messages
                self._check_unread_messages()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load friend data: {e}")
    
    def _on_friend_select(self, event):
        """When user selects a friend"""
        selection = self.friends_list.curselection()
        if not selection:
            return
            
        friend = self.friends_list.get(selection[0])
        self.current_chat = friend
        
        # Load chat history
        self._load_chat_history(friend)
    
    def _load_chat_history(self, friend):
        """Load chat history with a specific friend"""
        # Clear chat area
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        
        try:
            response = requests.get(
                f"{SERVER_URL}{MESSAGES_ENDPOINT.format(username=friend)}",
                params={"current_user": self.username}
            )
            
            if response.status_code == 200:
                messages = response.json()
                
                for msg in reversed(messages):  # Display from old to new
                    sender = msg["sender"]
                    content = msg["content"]
                    timestamp = msg["timestamp"]
                    
                    # Format timestamp
                    dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    time_str = dt.strftime("%H:%M:%S")
                    
                    # Set different styles based on sender
                    if sender == self.username:
                        self.chat_area.insert(tk.END, f"Me ({time_str}): ", "me")
                    else:
                        self.chat_area.insert(tk.END, f"{sender} ({time_str}): ", "other")
                    
                    self.chat_area.insert(tk.END, f"{content}\n")
        
        except Exception as e:
            self.chat_area.insert(tk.END, f"Failed to load chat history: {e}\n")
        
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)  # Scroll to bottom
    
    def _send_message(self, event=None):
        """Send message"""
        if not self.current_chat:
            messagebox.showinfo("Notice", "Please select a chat partner first")
            return
            
        content = self.msg_entry.get().strip()
        if not content:
            return
            
        try:
            response = requests.post(
                f"{SERVER_URL}{SEND_MESSAGE_ENDPOINT}",
                json={
                    "sender": self.username,
                    "receiver": self.current_chat,
                    "content": content
                }
            )
            
            if response.status_code == 201:
                # Clear input box
                self.msg_entry.delete(0, tk.END)
                
                # If there's a socket connection, send real-time message
                if self.socketio:
                    self.socketio.emit('send_message', {
                        "sender": self.username,
                        "receiver": self.current_chat,
                        "content": content
                    })
                
                # Refresh chat history
                self._load_chat_history(self.current_chat)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")
    
    def _add_friend(self):
        """Add friend"""
        username = simpledialog.askstring("Add Friend", "Please enter username:")
        if not username:
            return
            
        # Check if it's yourself
        if username == self.username:
            messagebox.showinfo("Notice", "You cannot add yourself as a friend")
            return
            
        try:
            # Send friend request
            response = requests.post(
                f"{SERVER_URL}{FRIEND_REQUEST_ENDPOINT}",
                json={"from_user": self.username, "to_user": username}
            )
            
            if response.status_code == 201:
                messagebox.showinfo("Success", f"Friend request sent to {username}")
                
                # If there's a socket connection, send real-time notification
                if self.socketio:
                    self.socketio.emit('friend_request', {
                        "from_user": self.username,
                        "to_user": username
                    })
            elif response.status_code == 409:
                messagebox.showinfo("Notice", "Already friends or request already sent")
            else:
                messagebox.showerror("Error", f"Request failed: {response.text}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send friend request: {e}")
    
    def _show_friend_requests(self):
        """Show friend requests"""
        try:
            response = requests.get(
                f"{SERVER_URL}{FRIENDS_LIST_ENDPOINT}",
                params={"username": self.username}
            )
            
            if response.status_code == 200:
                data = response.json()
                requests_list = data.get("requests", [])
                
                if not requests_list:
                    messagebox.showinfo("Friend Requests", "No pending friend requests")
                    return
                    
                # Create a new window to display requests
                req_window = tk.Toplevel(self.root)
                req_window.title("Friend Requests")
                req_window.geometry("300x250")
                
                # Request list
                ttk.Label(req_window, text="Pending friend requests:").pack(pady=5)
                req_listbox = tk.Listbox(req_window)
                req_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
                
                for req in requests_list:
                    username, timestamp = req
                    req_listbox.insert(tk.END, username)
                
                # Button frame
                btn_frame = ttk.Frame(req_window)
                btn_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Accept button
                def accept_selected():
                    selection = req_listbox.curselection()
                    if not selection:
                        messagebox.showinfo("Notice", "Please select a request first")
                        return
                        
                    from_user = req_listbox.get(selection[0])
                    
                    try:
                        response = requests.post(
                            f"{SERVER_URL}{ACCEPT_FRIEND_ENDPOINT}",
                            json={"from_user": from_user, "to_user": self.username}
                        )
                        
                        if response.status_code == 200:
                            messagebox.showinfo("Success", f"Accepted friend request from {from_user}")
                            req_listbox.delete(selection[0])
                            
                            # Refresh friends list
                            self._load_data()
                            
                            # If the list is empty, close the window
                            if req_listbox.size() == 0:
                                req_window.destroy()
                    
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to process friend request: {e}")
                
                # Reject button
                def reject_selected():
                    selection = req_listbox.curselection()
                    if not selection:
                        messagebox.showinfo("Notice", "Please select a request first")
                        return
                        
                    from_user = req_listbox.get(selection[0])
                    
                    try:
                        response = requests.post(
                            f"{SERVER_URL}{REJECT_FRIEND_ENDPOINT}",
                            json={"from_user": from_user, "to_user": self.username}
                        )
                        
                        if response.status_code == 200:
                            messagebox.showinfo("Success", f"Rejected friend request from {from_user}")
                            req_listbox.delete(selection[0])
                            
                            # If the list is empty, close the window
                            if req_listbox.size() == 0:
                                req_window.destroy()
                    
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to process friend request: {e}")
                
                ttk.Button(btn_frame, text="Accept", command=accept_selected).pack(side=tk.LEFT, padx=5)
                ttk.Button(btn_frame, text="Reject", command=reject_selected).pack(side=tk.LEFT, padx=5)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get friend requests: {e}")
    
    def _check_unread_messages(self):
        """Check for unread messages"""
        try:
            response = requests.get(
                f"{SERVER_URL}{UNREAD_COUNT_ENDPOINT}",
                params={"username": self.username}
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                
                if count > 0:
                    messagebox.showinfo("New Messages", f"You have {count} unread messages")
        
        except Exception as e:
            print(f"Failed to check unread messages: {e}")
    
    def _setup_socket_events(self):
        """Set up socket event handling"""
        # Send authentication
        self.socketio.emit('authenticate', {"username": self.username})
        
        # Handle new messages
        @self.socketio.on('new_message')
        def on_new_message(data):
            sender = data.get("sender")
            
            # If currently chatting with the sender, refresh chat history
            if self.current_chat == sender:
                self._load_chat_history(sender)
            else:
                messagebox.showinfo("New Message", f"New message from {sender}")
        
        # Handle friend requests
        @self.socketio.on('friend_request')
        def on_friend_request(data):
            from_user = data.get("from_user")
            messagebox.showinfo("Friend Request", f"{from_user} sent you a friend request")
    
    def _back_to_menu(self):
        """Return to main menu"""
        from app.controller.client_controller import _on_login
        _on_login(self.root, self.username) 