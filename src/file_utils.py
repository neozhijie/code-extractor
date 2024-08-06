import os
import PyPDF2
from typing import Set, List, Callable
from src.file_node import FileNode
from src.logger import logger
from src.config import CODE_FILE_EXTENSIONS

def get_code_extensions() -> Set[str]:
    return CODE_FILE_EXTENSIONS

def is_code_file(filename: str, custom_extensions: Set[str] = set()) -> bool:
    """Check if the file is a code file based on its extension."""
    extensions = get_code_extensions().union(custom_extensions)
    return any(filename.lower().endswith(ext) for ext in extensions)

def scan_directory(path: str, progress_callback: Callable[[str], None] = None) -> FileNode:
    root = FileNode(path)
    stack = [root]
    
    while stack:
        node = stack.pop()
        try:
            with os.scandir(node.path) as entries:
                for entry in entries:
                    child = FileNode(entry.path, parent=node)
                    node.children.append(child)
                    if child.is_dir:
                        stack.append(child)
                    if progress_callback:
                        progress_callback(entry.path)
        except PermissionError:
            logger.error(f"Permission denied: {node.path}")
        except Exception as e:
            logger.error(f"Error scanning directory {node.path}: {str(e)}")
    
    return root

def filter_files(node: FileNode, include_extensions: Set[str] = set(), exclude_extensions: Set[str] = set()) -> List[str]:
    filtered_files = []
    
    if node.is_dir:
        for child in node.children:
            filtered_files.extend(filter_files(child, include_extensions, exclude_extensions))
    else:
        _, ext = os.path.splitext(node.path)
        if (not include_extensions or ext in include_extensions) and ext not in exclude_extensions:
            filtered_files.append(node.path)
    
    return filtered_files

def extract_pdf_content(file_path: str) -> str:
    content = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                content += page.extract_text() + "\n"
    except Exception as e:
        content = f"Error extracting PDF content: {str(e)}"
    return content
