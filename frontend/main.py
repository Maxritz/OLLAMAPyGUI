import tkinter as tk
from gui.app_window import OllamaGUI

def main():
    root = tk.Tk()
    app = OllamaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()