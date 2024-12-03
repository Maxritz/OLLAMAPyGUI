# ========== START OF PART 1 ==========
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import os
from PIL import Image
try:
    import pytesseract
except ImportError:
    pytesseract = None
import PyPDF2
import pandas as pd
import docx
import io
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import threading
from queue import Queue
import validators
from urllib.parse import urlparse

class ChatFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_model = None
        self.file_content = None
        self.current_file = None
        self.knowledge_base = []
        self.url_history = []
        self.processing_queue = Queue()
        self.create_widgets()
        self.start_processing_thread()
# ========== END OF PART 1 ==========
# ========== START OF PART 2 ==========
    def create_widgets(self):
        # Main split view
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left side - Chat area
        self.chat_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.chat_frame)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            bg='white',
            height=20
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Input area
        self.input_frame = ttk.Frame(self.chat_frame)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.message_input = scrolledtext.ScrolledText(
            self.input_frame,
            height=3,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.message_input.bind('<Return>', self.handle_return)
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)

        # Right side - Knowledge Base
        self.kb_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.kb_frame)

        # Create Knowledge Base Controls
        self.create_kb_controls()

    def create_kb_controls(self):
        # File Upload Section
        file_frame = ttk.LabelFrame(self.kb_frame, text="Document Upload")
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(file_frame, text="Upload Document", 
                  command=self.attach_file).pack(fill=tk.X, padx=5, pady=2)
        
        self.file_label = ttk.Label(file_frame, text="No file attached")
        self.file_label.pack(fill=tk.X, padx=5, pady=2)

        # URL Section
        url_frame = ttk.LabelFrame(self.kb_frame, text="URL Processing")
        url_frame.pack(fill=tk.X, padx=5, pady=5)

        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(fill=tk.X, padx=5, pady=2)

        url_buttons = ttk.Frame(url_frame)
        url_buttons.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(url_buttons, text="Add URL", 
                  command=self.add_url).pack(side=tk.LEFT, padx=2)
        ttk.Button(url_buttons, text="Batch URLs", 
                  command=self.batch_urls).pack(side=tk.LEFT, padx=2)

        # RAG Settings
        rag_frame = ttk.LabelFrame(self.kb_frame, text="Knowledge Base Settings")
        rag_frame.pack(fill=tk.X, padx=5, pady=5)

        # Context settings
        ttk.Label(rag_frame, text="Context Size:").pack(padx=5, pady=2)
        self.context_size = ttk.Scale(rag_frame, from_=1, to=10, orient=tk.HORIZONTAL)
        self.context_size.set(4)
        self.context_size.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(rag_frame, text="Relevance Threshold:").pack(padx=5, pady=2)
        self.relevance_threshold = ttk.Scale(rag_frame, from_=0, to=1, orient=tk.HORIZONTAL)
        self.relevance_threshold.set(0.7)
        self.relevance_threshold.pack(fill=tk.X, padx=5, pady=2)

        # RAG toggle
        self.use_rag = tk.BooleanVar(value=True)
        ttk.Checkbutton(rag_frame, text="Use Knowledge Base", 
                       variable=self.use_rag).pack(padx=5, pady=5)

        # Knowledge Base Content
        kb_content = ttk.LabelFrame(self.kb_frame, text="Knowledge Base Contents")
        kb_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for knowledge base entries
        self.kb_tree = ttk.Treeview(
            kb_content,
            columns=("Source", "Size", "Date"),
            show="headings"
        )
        
        self.kb_tree.heading("Source", text="Source")
        self.kb_tree.heading("Size", text="Size")
        self.kb_tree.heading("Date", text="Date Added")
        
        self.kb_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Control buttons
        kb_buttons = ttk.Frame(kb_content)
        kb_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(kb_buttons, text="Remove Selected", 
                  command=self.remove_kb_entry).pack(side=tk.LEFT, padx=2)
        ttk.Button(kb_buttons, text="Clear All", 
                  command=self.clear_kb).pack(side=tk.LEFT, padx=2)
# ========== END OF PART 2 ==========
# ========== START OF PART 3A ==========
    def start_processing_thread(self):
        def process_queue():
            while True:
                try:
                    func, args = self.processing_queue.get()
                    func(*args)
                    self.processing_queue.task_done()
                except Exception as e:
                    self.add_system_message(f"Error in processing: {str(e)}")

        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()

    def handle_return(self, event):
        if not event.state & 0x1:  # Shift not pressed
            self.send_message()
            return 'break'
        return None

    def attach_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All supported", "*.txt *.pdf *.docx *.csv *.jpg *.jpeg *.png"),
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("CSV files", "*.csv"),
                ("Images", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        try:
            filename = os.path.basename(file_path)
            extension = os.path.splitext(file_path)[1].lower()

            if extension == '.pdf':
                content = self.read_pdf(file_path)
            elif extension == '.docx':
                content = self.read_docx(file_path)
            elif extension == '.csv':
                content = self.read_csv(file_path)
            elif extension in ['.jpg', '.jpeg', '.png']:
                content = self.read_image(file_path)
            else:
                content = self.read_text(file_path)

            self.add_to_kb(content, f"File: {filename}")
            self.file_label.config(text=f"Added: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not process file: {str(e)}")

    def read_pdf(self, file_path):
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return "\n".join(page.extract_text() for page in reader.pages)

    def read_docx(self, file_path):
        doc = docx.Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    def read_csv(self, file_path):
        df = pd.read_csv(file_path)
        return df.to_string()

    def read_image(self, file_path):
        if pytesseract is None:
            return "OCR not available. Please install pytesseract."
        try:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            return f"Failed to process image: {str(e)}"

    def read_text(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
# ========== END OF PART 3A ==========
# ========== START OF PART 3B ==========
    def add_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        if not validators.url(url):
            messagebox.showwarning("Warning", "Invalid URL")
            return

        self.processing_queue.put((self.process_url, [url]))
        self.url_entry.delete(0, tk.END)
        self.add_system_message(f"Processing URL: {url}")

    def process_url(self, url):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Clean content
            for tag in soup(['script', 'style']):
                tag.decompose()
            
            text = soup.get_text(separator='\n')
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = '\n'.join(lines)
            
            self.add_to_kb(content, f"URL: {url}")
            
        except Exception as e:
            self.add_system_message(f"Failed to process {url}: {str(e)}")

    def batch_urls(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if validators.url(line.strip())]
            
            if not urls:
                messagebox.showwarning("Warning", "No valid URLs found")
                return

            for url in urls:
                self.processing_queue.put((self.process_url, [url]))
            
            self.add_system_message(f"Processing {len(urls)} URLs...")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process URLs: {str(e)}")

    def add_to_kb(self, content, source):
        entry = {
            'content': content,
            'source': source,
            'date': datetime.now(),
            'size': len(content)
        }
        self.knowledge_base.append(entry)
        self.update_kb_view()

    def update_kb_view(self):
        for item in self.kb_tree.get_children():
            self.kb_tree.delete(item)
        
        for entry in self.knowledge_base:
            self.kb_tree.insert('', 'end', values=(
                entry['source'],
                f"{entry['size']/1024:.1f} KB",
                entry['date'].strftime("%Y-%m-%d %H:%M")
            ))

    def remove_kb_entry(self):
        selected = self.kb_tree.selection()
        if not selected:
            return
        
        for item in selected:
            idx = self.kb_tree.index(item)
            if 0 <= idx < len(self.knowledge_base):
                del self.knowledge_base[idx]
        
        self.update_kb_view()

    def clear_kb(self):
        if messagebox.askyesno("Confirm", "Clear entire knowledge base?"):
            self.knowledge_base.clear()
            self.update_kb_view()
# ========== END OF PART 3B ==========
# ========== START OF PART 3C ==========
    def set_model(self, model_name):
        self.current_model = model_name
        if model_name:
            self.add_system_message(f"Using model: {model_name}")
        else:
            self.add_system_message("No model loaded")

    def process_with_rag(self, message):
        if not self.use_rag.get() or not self.knowledge_base:
            return message

        context_size = int(self.context_size.get())
        threshold = self.relevance_threshold.get()

        relevant_contexts = []
        for entry in self.knowledge_base:
            if any(term.lower() in entry['content'].lower() for term in message.split()):
                preview = entry['content'][:500]  # Larger context window
                relevant_contexts.append(f"From {entry['source']}:\n{preview}")
                if len(relevant_contexts) >= context_size:
                    break

        if relevant_contexts:
            context_text = "\n\n".join(relevant_contexts)
            return f"""Using knowledge base with {len(relevant_contexts)} relevant contexts:

{context_text}

Question: {message}"""
        return message

    def send_message(self):
        if not self.current_model:
            messagebox.showwarning("Warning", "Please load a model first")
            return

        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return

        # Disable input while processing
        self.message_input.configure(state=tk.DISABLED)
        self.send_button.configure(state=tk.DISABLED)
        
        # Process with RAG if enabled
        full_message = self.process_with_rag(message)

        # Show user message
        self.add_message("You", message)
        self.message_input.delete("1.0", tk.END)

        try:
            # Send to Ollama
            result = subprocess.run(
                ['ollama', 'run', self.current_model],
                input=full_message,
                text=True,
                capture_output=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                self.add_message("Assistant", result.stdout.strip())
            else:
                self.add_system_message(f"Error: {result.stderr}")
        except Exception as e:
            self.add_system_message(f"Error: {str(e)}")
        finally:
            # Re-enable input
            self.message_input.configure(state=tk.NORMAL)
            self.send_button.configure(state=tk.NORMAL)
            self.message_input.focus()

    def add_message(self, sender, message):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n{sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)

    def add_system_message(self, message):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\nSystem: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)
# ========== END OF PART 3C ==========