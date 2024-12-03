# database/db_manager.py
import sqlite3
from datetime import datetime

class DatabaseManager:
    def add_interaction_metrics(self, model_name, prompt, response, tokens_used, response_time, success_rate):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO model_metrics 
                (timestamp, model_name, prompt_length, response_length, tokens_used, 
                response_time, success_rate) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), model_name, len(prompt), len(response),
                tokens_used, response_time, success_rate
            ))

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME,
                    model TEXT,
                    message TEXT,
                    response TEXT,
                    tokens INTEGER,
                    response_time FLOAT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_metrics (
                    id INTEGER PRIMARY KEY,
                    model TEXT,
                    date DATE,
                    total_tokens INTEGER,
                    avg_response_time FLOAT,
                    total_conversations INTEGER
                )
            ''')
            
            conn.commit()

    def add_chat_entry(self, model, message, response, tokens, response_time):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (timestamp, model, message, response, tokens, response_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), model, message, response, tokens, response_time))
            conn.commit()
