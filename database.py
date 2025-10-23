import sqlite3
import logging
from datetime import datetime

class Database:
    def __init__(self, db_path='content.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posted_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_content_posted(self, url):
        """Проверяет, был ли контент уже опубликован"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM posted_content WHERE url = ?', (url,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def mark_as_posted(self, title, url, category):
        """Помечает контент как опубликованный"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
 
        try:
            cursor.execute('''
                INSERT INTO posted_content (title, url, category)
                VALUES (?, ?, ?)
            ''', (title, url, category))
            conn.commit()
        except sqlite3.IntegrityError:
            # URL уже существует
            pass
        finally:
            conn.close()
