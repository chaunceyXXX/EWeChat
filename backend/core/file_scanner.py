import os
import glob
from typing import Optional

class FileScanner:
    @staticmethod
    def get_latest_file(directory_path: str, file_pattern: str = "*") -> Optional[str]:
        """
        Get the latest file in the directory.
        Ignores directories and hidden files (starting with .).
        """
        if not directory_path or not os.path.exists(directory_path):
            return None

        # Construct search pattern
        search_path = os.path.join(directory_path, file_pattern)
        files = glob.glob(search_path)
        
        # Filter out directories and hidden files
        files = [f for f in files if os.path.isfile(f) and not os.path.basename(f).startswith('.')]

        if not files:
            return None

        # Sort by modification time, descending
        try:
            latest_file = max(files, key=os.path.getmtime)
            return latest_file
        except Exception as e:
            print(f"Error finding latest file: {e}")
            return None
