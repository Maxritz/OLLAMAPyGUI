# gui/frames/model_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

class ModelFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.loaded_model = None
        self.create_widgets()
        self.refresh_models()

    def create_widgets(self):
        # Title
        ttk.Label(self, text="Model Management", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Model list
        self.model_list = tk.Listbox(self, height=10, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.model_list.yview)
        self.model_list.configure(yscrollcommand=scrollbar.set)
        
        self.model_list.pack(fill=tk.X, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        ttk.Button(self, text="Refresh Models", command=self.refresh_models).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self, text="Load Model", command=self.load_model).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(self, text="Unload Model", command=self.unload_model).pack(fill=tk.X, padx=5, pady=2)
        
        # Add refresh controls
        refresh_frame = ttk.LabelFrame(self, text="Model Controls")
        refresh_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(refresh_frame, text="Refresh Model", 
                  command=self.refresh_model).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(refresh_frame, text="Clear Context", 
                  command=self.clear_context).pack(fill=tk.X, padx=5, pady=2)
        
        # Status
        self.status_frame = ttk.LabelFrame(self, text="Model Status")
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(self.status_frame, text="No model loaded")
        self.status_label.pack(padx=5, pady=5)

    def refresh_models(self):
        self.model_list.delete(0, tk.END)
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                # Skip header line and process model names
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        self.model_list.insert(tk.END, model_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get models: {str(e)}")

    def load_model(self):
        selection = self.model_list.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a model")
            return
            
        model_name = self.model_list.get(selection[0])
        
        if self.loaded_model == model_name:
            messagebox.showinfo("Info", f"Model {model_name} is already loaded")
            return

        try:
            self.status_label.config(text=f"Loading {model_name}...")
            self.update()
            
            # Test if model loads correctly
            result = subprocess.run(
                ['ollama', 'run', model_name, '--nowordwrap'],
                input='test',
                text=True,
                capture_output=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                self.loaded_model = model_name
                self.status_label.config(text=f"Model: {model_name} (Loaded)")
                self.controller.chat_frame.set_model(model_name)
                messagebox.showinfo("Success", f"Model {model_name} loaded successfully")
            else:
                self.status_label.config(text="Load failed")
                messagebox.showerror("Error", f"Failed to load model: {result.stderr}")
        except Exception as e:
            self.status_label.config(text="Load failed")
            messagebox.showerror("Error", f"Error loading model: {str(e)}")

    def unload_model(self):
        if not self.loaded_model:
            messagebox.showinfo("Info", "No model is currently loaded")
            return
        
        self.loaded_model = None
        self.status_label.config(text="No model loaded")
        self.controller.chat_frame.set_model(None)
        messagebox.showinfo("Success", "Model unloaded")

    def refresh_model(self):
        try:
            model_name = self.loaded_model
            if model_name:
                subprocess.run(['ollama', 'pull', model_name])
                messagebox.showinfo("Success", f"Model {model_name} refreshed")
            else:
                messagebox.showwarning("Warning", "No model is currently loaded")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh model: {str(e)}")

    def clear_context(self):
        if self.loaded_model:
            self.controller.chat_frame.chat_display.configure(state=tk.NORMAL)
            self.controller.chat_frame.chat_display.delete("1.0", tk.END)
            self.controller.chat_frame.chat_display.configure(state=tk.DISABLED)
            self.controller.chat_frame.add_system_message("Context cleared")
        else:
            messagebox.showwarning("Warning", "No model is currently loaded")