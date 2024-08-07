import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, BooleanVar
from tkinter.scrolledtext import ScrolledText
from typing import List
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from src.file_utils import scan_directory, is_code_file, extract_pdf_content
from src.logger import logger
import io

class CodeExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CodeExtractor - Select and Extract Code Files")
        self.root.geometry("1000x700")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.is_dark_mode = BooleanVar(value=False)
        self.create_menu()

        self.setup_ui()
        self.file_tree = None
        self.root_path = ""
        self.queue = queue.Queue()
        self.process_queue()

    def setup_ui(self):
        self.create_path_frame()
        self.create_main_frame()
        self.create_button_frame()
        self.create_progress_bar()
        self.apply_light_theme()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.is_dark_mode, command=self.toggle_dark_mode)

    def toggle_dark_mode(self):
        if self.is_dark_mode.get():
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def apply_dark_theme(self):
        self.style.theme_use('clam')
        self.style.configure(".", background="#2E2E2E", foreground="#FFFFFF")
        self.style.configure("Treeview", background="#2E2E2E", foreground="#FFFFFF", fieldbackground="#2E2E2E")
        self.style.map("Treeview", background=[('selected', '#4A6984')])
        self.style.configure("TEntry", fieldbackground="#3E3E3E", foreground="#FFFFFF")
        self.style.configure("TButton", background="#3E3E3E", foreground="#FFFFFF")
        self.style.map("TButton", background=[('active', '#4A6984')])
        self.preview_text.config(bg="#2E2E2E", fg="#FFFFFF")
        self.root.configure(bg="#2E2E2E")
        self.tree.tag_configure("checked", foreground="#FFFFFF")  
        self.tree.tag_configure("unchecked", foreground="#FFFFFF")
        self.tree.tag_configure("match", background="#6A5ACD")

    def apply_light_theme(self):
        self.style.theme_use('clam')
        self.style.configure(".", background="SystemButtonFace", foreground="SystemWindowText")
        self.style.configure("Treeview", background="SystemButtonFace", foreground="SystemWindowText", fieldbackground="SystemButtonFace")
        self.style.map("Treeview", background=[('selected', 'SystemHighlight')])
        self.style.configure("TEntry", fieldbackground="SystemWindow", foreground="SystemWindowText")
        self.style.configure("TButton", background="SystemButtonFace", foreground="SystemWindowText")
        self.style.map("TButton", background=[('active', 'SystemHighlight')])
        self.preview_text.config(bg="SystemWindow", fg="SystemWindowText")
        self.root.configure(bg="SystemButtonFace")
        self.tree.tag_configure("checked", foreground="blue")
        self.tree.tag_configure("unchecked", foreground="black")
        self.tree.tag_configure("match", background="yellow")


    def create_path_frame(self):
        path_frame = ttk.Frame(self.root)
        path_frame.pack(fill="x", pady=10, padx=10)

        self.path_entry = ttk.Entry(path_frame)
        self.path_entry.pack(side="left", expand=True, fill="x")
        self.path_entry.bind("<Return>", self.on_path_enter)

        browse_btn = ttk.Button(path_frame, text="Browse", command=self.browse_directory)
        browse_btn.pack(side="left", padx=5)
    

    def on_path_enter(self, event):
        entered_path = self.path_entry.get()
        if os.path.isdir(entered_path):
            self.root_path = entered_path
            self.start_scanning_thread()
        else:
            messagebox.showerror(
                "Invalid Path", "The entered path is not a valid directory."
            )

    def create_main_frame(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Left side: Treeview and Search
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", expand=True, fill="both")

        # Search functionality
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill="x", pady=5)

        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", expand=True, fill="x")

        search_btn = ttk.Button(search_frame, text="Search", command=self.search_tree)
        search_btn.pack(side="left", padx=5)

        # Treeview
        self.tree = ttk.Treeview(left_frame, columns=("check",))
        self.tree.heading("#0", text="File Structure")
        self.tree.heading("check", text="Select")
        self.tree.column("check", width=50, anchor="center")
        self.tree.pack(expand=True, fill="both")

        self.tree.tag_configure("checked", foreground="blue")
        self.tree.tag_configure("unchecked", foreground="black")
        self.tree.tag_configure("match", background="yellow")

        self.tree.bind("<ButtonRelease-1>", self.on_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Right side: Preview
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", expand=True, fill="both", padx=(10, 0))

        preview_label = ttk.Label(right_frame, text="File Preview:")
        preview_label.pack(anchor="w")

        self.preview_text = ScrolledText(
            right_frame, wrap=tk.WORD, width=50, height=20
        )
        self.preview_text.pack(expand=True, fill="both")

    def create_button_frame(self):
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", pady=10)

        extract_btn = ttk.Button(
            btn_frame, text="Extract Selected", command=self.extract_selected
        )
        extract_btn.pack(side="right", padx=10)

    def create_progress_bar(self):
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(fill="x", pady=10, padx=10)

        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient="horizontal", length=300, mode="determinate"
        )
        self.progress_bar.pack(side="left", expand=True, fill="x")

        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(side="left", padx=5)

        self.progress_frame.pack_forget()  # Hide initially

    def browse_directory(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)
            self.root_path = folder_path
            self.start_scanning_thread()

    def start_scanning_thread(self):
        self.progress_frame.pack(fill="x", pady=10, padx=10)  # Show progress bar
        self.progress_bar["value"] = 0
        self.progress_label["text"] = "Scanning directory..."
        scanning_thread = threading.Thread(target=self.scan_and_populate)
        scanning_thread.start()

    def scan_and_populate(self):
        try:
            total_items = sum(
                [len(files) + len(dirs) for _, dirs, files in os.walk(self.root_path)]
            )
            scanned_items = 0

            def progress_callback(item):
                nonlocal scanned_items
                scanned_items += 1
                progress = int((scanned_items / total_items) * 100)
                self.queue.put(("update_progress", progress))

            self.file_tree = scan_directory(self.root_path, progress_callback)
            self.queue.put(("populate", None))
        except Exception as e:
            logger.error(f"Error scanning directory: {str(e)}")
            self.queue.put(("error", str(e)))
        finally:
            self.queue.put(("hide_progress", None))

    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        def insert_node(parent, node):
            tree_node = self.tree.insert(
                parent,
                "end",
                text=node.name,
                open=False,
                values=("☑",),
                tags=("checked",),
            )
            node.tree_id = tree_node
            for child in node.children:
                insert_node(tree_node, child)

        insert_node("", self.file_tree)

    def on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # The 'check' column
                item = self.tree.identify_row(event.y)
                self.toggle_check(item)

    def toggle_check(self, item):
        current_value = self.tree.item(item, "values")[0]
        new_value = "☐" if current_value == "☑" else "☑"
        self.tree.item(item, values=(new_value,))
        new_tag = "unchecked" if new_value == "☐" else "checked"
        self.tree.item(item, tags=(new_tag,))
        logger.debug(
            f"Toggled item: {self.tree.item(item, 'text')}, New value: {new_value}"
        )
        self.update_children(item, new_value)
        self.update_parents(self.tree.parent(item))

    def update_children(self, parent, value):
        for child in self.tree.get_children(parent):
            self.tree.item(child, values=(value,))
            tag = "checked" if value == "☑" else "unchecked"
            self.tree.item(child, tags=(tag,))
            self.update_children(child, value)

    def update_parents(self, parent):
        if parent:
            children = self.tree.get_children(parent)
            all_checked = all(
                self.tree.item(child, "values")[0] == "☑" for child in children
            )
            new_value = "☑" if all_checked else "☐"
            self.tree.item(parent, values=(new_value,))
            tag = "checked" if new_value == "☑" else "unchecked"
            self.tree.item(parent, tags=(tag,))
            self.update_parents(self.tree.parent(parent))

    def get_selected_files(self, item):
        selected_files = []
        value = self.tree.item(item, "values")[0]
        logger.debug(f"Checking item: {self.tree.item(item, 'text')}, Value: {value}")

        item_path = self.get_item_path(item)
        logger.debug(f"Constructed path: {item_path}")

        if value == "☑":
            selected_files.append(item_path)
            logger.debug(f"Added item: {item_path}")

        for child in self.tree.get_children(item):
            selected_files.extend(self.get_selected_files(child))

        return selected_files

    def get_item_path(self, item):
        path_parts = []
        current_item = item
        while current_item:
            item_text = self.tree.item(current_item, "text")
            path_parts.insert(0, item_text)
            current_item = self.tree.parent(current_item)

        # Remove the root directory name from the path parts
        if path_parts and path_parts[0] == os.path.basename(self.root_path):
            path_parts.pop(0)

        full_path = os.path.join(self.root_path, *path_parts)
        logger.debug(f"Constructed full path: {full_path}")
        return full_path

    def extract_selected(self):
        root_item = self.tree.get_children()[0]
        logger.debug(f"Root item: {self.tree.item(root_item, 'text')}")
        logger.debug(f"Root path: {self.root_path}")
        selected_items = self.get_selected_files(root_item)
        logger.debug(f"Number of selected items: {len(selected_items)}")
        logger.debug(f"Selected items: {selected_items}")

        if not selected_items:
            messagebox.showwarning("No Selection", "No items selected for extraction.")
            return

        output_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )

        if output_file:
            self.progress_frame.pack(fill="x", pady=10, padx=10)  # Show progress bar
            self.progress_bar["value"] = 0
            self.progress_label["text"] = "Extracting files..."
            threading.Thread(
                target=self.extract_files, args=(selected_items, output_file)
            ).start()

    def extract_files(self, selected_items: List[str], output_file: str):
        try:
            total_items = len(selected_items)
            buffer = io.StringIO()
            
            def process_file(item_path):
                relative_path = os.path.relpath(item_path, self.root_path)
                content = ""
                if os.path.isfile(item_path):
                    content += f"File: {relative_path}\n"
                    content += "-" * 80 + "\n"
                    if is_code_file(item_path):
                        if item_path.lower().endswith(".pdf"):
                            content += extract_pdf_content(item_path)
                        else:
                            try:
                                with open(item_path, "r", encoding="utf-8") as code_file:
                                    content += code_file.read()
                            except UnicodeDecodeError:
                                content += "Unable to read file: encoding error\n"
                            except Exception as e:
                                content += f"Error reading file: {str(e)}\n"
                    else:
                        content += "Non-code file (content not extracted)\n"
                    content += "\n\n"
                else:
                    content += f"Directory: {relative_path}\n"
                    content += "-" * 80 + "\n\n"
                return content

            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                futures = [executor.submit(process_file, item_path) for item_path in selected_items]
                for i, future in enumerate(futures):
                    buffer.write(future.result())
                    progress = int(((i + 1) / total_items) * 100)
                    self.queue.put(("update_progress", progress))

            with open(output_file, "w", encoding="utf-8") as out_file:
                out_file.write(buffer.getvalue())

            self.queue.put(("extraction_complete", output_file))
        except Exception as e:
            self.queue.put(("extraction_error", str(e)))
        finally:
            self.queue.put(("hide_progress", None))

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            item_path = self.get_item_path(item)
            self.preview_file(item_path)

    def preview_file(self, file_path):
        self.preview_text.delete("1.0", tk.END)
        if os.path.isfile(file_path):
            try:
                if file_path.lower().endswith(".pdf"):
                    content = extract_pdf_content(file_path)[:4000]  # First 4000 characters
                    self.preview_text.insert(tk.END, content)
                    if len(content) == 4000:
                        self.preview_text.insert(tk.END, "\n\n[File truncated...]")
                else:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read(4000)  # Read first 4000 characters
                        self.preview_text.insert(tk.END, content)
                        if len(content) == 4000:
                            self.preview_text.insert(tk.END, "\n\n[File truncated...]")
            except UnicodeDecodeError:
                self.preview_text.insert(tk.END, "Unable to preview: encoding error")
            except Exception as e:
                self.preview_text.insert(tk.END, f"Error previewing file: {str(e)}")
        elif os.path.isdir(file_path):
            self.preview_text.insert(tk.END, f"Selected item is a directory: {file_path}")
        else:
            self.preview_text.insert(tk.END, f"Item not found: {file_path}")

        logger.debug(f"Previewing: {file_path}")

    def search_tree(self):
        query = self.search_entry.get().lower()
        if not query:
            return

        def search_recursive(item):
            item_text = self.tree.item(item, "text").lower()
            if query in item_text:
                self.tree.item(item, tags=("match",))
                self.tree.see(item)
            else:
                self.tree.item(item, tags=())

            for child in self.tree.get_children(item):
                search_recursive(child)

        root_item = self.tree.get_children()[0]
        search_recursive(root_item)


    def process_queue(self):
        try:
            while True:
                action, data = self.queue.get_nowait()
                if action == "populate":
                    self.populate_tree()
                elif action == "error":
                    messagebox.showerror("Error", f"Failed to scan directory: {data}")
                elif action == "update_progress":
                    self.progress_bar["value"] = data
                    self.progress_label["text"] = f"Progress: {data}%"
                elif action == "hide_progress":
                    self.progress_frame.pack_forget()
                elif action == "extraction_complete":
                    messagebox.showinfo(
                        "Extraction Complete",
                        f"Selected items have been extracted to {data}",
                    )
                elif action == "extraction_error":
                    messagebox.showerror(
                        "Extraction Error",
                        f"An error occurred during extraction: {data}",
                    )
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = CodeExtractorGUI(root)
    root.mainloop()
