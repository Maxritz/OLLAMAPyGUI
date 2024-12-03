# config/settings.py
import json
import os

class Settings:
    def __init__(self):
        self.config_file = 'config/config.json'
        self.default_settings = {
            'api_base': 'http://localhost:11434/api',
            'default_model': 'llama2-3.2-vision:latest',
            'temperature': 0.7,
            'max_tokens': 2000,
            'db_path': 'data/ollama_gui.db',
            'rag_settings': {
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'similarity_threshold': 0.7
            }
        }
        self.current_settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.default_settings.copy()

    def save_settings(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.current_settings, f, indent=4)