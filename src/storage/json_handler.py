import json
import os
import yaml
from datetime import datetime

class JSONHandler:
    def __init__(self):
        self.config = self._load_config()
        self.file_path = self.config.get('storage', {}).get('export_file', 'data/security_watch_log.json')
        self._ensure_file_exists()

    def _load_config(self):
        try:
            with open('config/settings.yaml', 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def _ensure_file_exists(self):
        if not os.path.exists(os.path.dirname(self.file_path)):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def append_item(self, item):
        """
        Reads the current list, checks for duplicates, appends new item, saves.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []

            # Check for duplicates based on link
            existing_links = {entry.get('link') for entry in data}
            
            if item.get('link') not in existing_links:
                # Add timestamp of capture if not present
                if 'captured_at' not in item:
                    item['captured_at'] = datetime.now().isoformat()
                
                data.append(item)
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            return False
        except Exception as e:
            print(f"Error saving to JSON: {e}")
            return False

    def get_file_path(self):
        return os.path.abspath(self.file_path)
