# storage.py
import json
import os
import logging
from typing import Any, Dict, List

class DataStorage:
    def __init__(self, base_dir: str = 'data'):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save_data(self, data: Any, filename: str) -> bool:
        """Save data to JSON file"""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"Data saved successfully to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error saving data to {filename}: {str(e)}")
            return False

    def load_data(self, filename: str) -> Any:
        """Load data from JSON file"""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading data from {filename}: {str(e)}")
            return None