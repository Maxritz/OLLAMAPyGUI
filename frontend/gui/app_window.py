import tkinter as tk
from tkinter import ttk
from .frames.model_frame import ModelFrame
from .frames.chat_frame import ChatFrame
from .frames.control_frame import ControlFrame

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat Interface")
        self.root.geometry("1200x800")
        
        # Initialize main container
        self.main_container = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create frames
        self.model_frame = ModelFrame(self.main_container, self)  # Pass self as controller
        self.main_container.add(self.model_frame)
        
        # Create right pane
        self.right_pane = ttk.PanedWindow(self.main_container, orient=tk.VERTICAL)
        self.main_container.add(self.right_pane)
        
        self.chat_frame = ChatFrame(self.right_pane, self)  # Pass self as controller
        self.right_pane.add(self.chat_frame)
        
        self.control_frame = ControlFrame(self.right_pane, self)  # Pass self as controller
        self.right_pane.add(self.control_frame)