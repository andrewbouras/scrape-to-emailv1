import json
import os
import logging

class EmailExporter:
    def __init__(self, base_dir: str = 'emails'):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save_emails(self, emails: dict, filename: str) -> bool:
        """Save emails to JSON file"""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(emails, f, indent=2)
            logging.info(f"Emails saved successfully to {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error saving emails to {filename}: {str(e)}")
            return False