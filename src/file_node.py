from typing import List, Optional
import os

class FileNode:
    def __init__(self, path: str, parent: Optional['FileNode'] = None):
        self.path: str = path
        self.parent: Optional['FileNode'] = parent
        self.children: List['FileNode'] = []
        self.tree_id: Optional[str] = None

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def is_dir(self) -> bool:
        return os.path.isdir(self.path)
