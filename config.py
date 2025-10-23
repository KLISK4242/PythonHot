import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Токен бота от @BotFather
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    # ID канала (например, @your_channel -> -1001234567890)
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    
    # Источники контента
    CONTENT_SOURCES = {
        'programming': [
            'https://habr.com/ru/rss/all/all/',
            'https://stackoverflow.blog/feed/',
            'https://realpython.com/atom.xml'
        ],
        'languages': [
            'https://www.fluentu.com/blog/feed/',
            'https://www.duolingo.com/feed'
        ],
        'history': [
            'https://www.history.com/news/feed',
            'https://www.historians.org/news/feed'
        ]
    }


    # Ключевые слова для фильтрации
    KEYWORDS = {
        'programming': ['python', 'javascript', 'java', 'c++'],
        'languages': ['english', 'spanish', 'french', 'german', 'grammar'],
        'history': ['ancient', 'medieval', 'modern history', 'world war',]
    }
