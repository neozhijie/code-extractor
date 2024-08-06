import tkinter as tk
from src.gui import CodeExtractorGUI
import os


def main():
    root = tk.Tk()
    root.title("CodeExtractor")

    # Set the app icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "codeExtractor.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)

    gui = CodeExtractorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
