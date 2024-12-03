# gui/frames/control_frame.py
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime

class ControlFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        self.create_settings(settings_frame)
        notebook.add(settings_frame, text="Settings")
        
        # Metrics tab
        metrics_frame = ttk.Frame(notebook)
        self.create_metrics(metrics_frame)
        notebook.add(metrics_frame, text="Metrics")

    def create_settings(self, parent):
        # Model Parameters
        param_frame = ttk.LabelFrame(parent, text="Model Parameters")
        param_frame.pack(fill=tk.X, padx=5, pady=5)

        # Temperature
        ttk.Label(param_frame, text="Temperature:").pack(padx=5, pady=2)
        temp_scale = ttk.Scale(param_frame, from_=0, to=1, orient=tk.HORIZONTAL)
        temp_scale.set(0.7)
        temp_scale.pack(fill=tk.X, padx=5, pady=2)

        # Max tokens
        ttk.Label(param_frame, text="Max Tokens:").pack(padx=5, pady=2)
        token_entry = ttk.Entry(param_frame)
        token_entry.insert(0, "2000")
        token_entry.pack(fill=tk.X, padx=5, pady=2)

        # Context window
        ttk.Label(param_frame, text="Context Window:").pack(padx=5, pady=2)
        context_entry = ttk.Entry(param_frame)
        context_entry.insert(0, "4096")
        context_entry.pack(fill=tk.X, padx=5, pady=2)

        # Save button
        ttk.Button(param_frame, text="Save Settings").pack(padx=5, pady=5)

    def create_metrics(self, parent):
        # Create metrics display frame
        metrics_display = ttk.LabelFrame(parent, text="Usage Metrics")
        metrics_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Date range selection
        date_frame = ttk.Frame(metrics_display)
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.start_date = DateEntry(date_frame)
        self.start_date.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.end_date = DateEntry(date_frame)
        self.end_date.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(date_frame, text="Update", command=self.update_metrics).pack(side=tk.LEFT, padx=5)

        # Metrics tree view
        self.metrics_tree = ttk.Treeview(metrics_display, columns=(
            "date", "tokens", "response_time", "success_rate"
        ), show="headings")
        
        # Configure columns
        self.metrics_tree.heading("date", text="Date")
        self.metrics_tree.heading("tokens", text="Tokens Used")
        self.metrics_tree.heading("response_time", text="Response Time")
        self.metrics_tree.heading("success_rate", text="Success Rate")
        
        # Configure scrollbar
        scrollbar = ttk.Scrollbar(metrics_display, orient="vertical", command=self.metrics_tree.yview)
        self.metrics_tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        self.metrics_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    def update_metrics(self):
        # Clear current items
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)
            
        # Add dummy data (replace with actual data from database)
        example_data = [
            ("2024-03-01", "1000", "0.5s", "95%"),
            ("2024-03-02", "1200", "0.6s", "93%"),
            ("2024-03-03", "900", "0.4s", "97%")
        ]
        
        for data in example_data:
            self.metrics_tree.insert("", tk.END, values=data)