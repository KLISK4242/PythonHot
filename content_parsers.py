import requests
import feedparser
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
import aiohttp
import asyncio

class ContentParser:
    def __init__(self, database):
        self.db = database
        self.logger = logging.getLogger(__name__)
    
    async def fetch_rss_feed(self, url):
        """Асинхронно получает RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()
                    return feedparser.parse(content)
        except Exception as e:
            self.logger.error(f"Error fetching RSS {url}: {e}")
            return None
    
    def parse_article_content(self, url):
        """Парсит полный текст статьи"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            # Ищем основной контент
            article = soup.find('article') or soup.find('div', class_=['content', 'article', 'post'])
            if article:
                text = article.get_text(strip=True, separator='\n')
            else:
                text = soup.get_text(strip=True, separator='\n')
            
            return ' '.join(text.split()[:500])  # Ограничиваем длину
        except Exception as e:
            self.logger.error(f"Error parsing article {url}: {e}")
            return None
    
    def is_recent(self, entry):
        """Проверяет, является ли запись свежей (последние 7 дней)"""
        if hasattr(entry, 'published_parsed'):
            publish_time = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed'):
            publish_time = datetime(*entry.updated_parsed[:6])
        else:
            return True  # Если даты нет, считаем свежим
        
        return publish_time > datetime.now() - timedelta(days=7)
    
    def matches_keywords(self, text, keywords):
        """Проверяет соответствие ключевым словам"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    async def get_content_for_category(self, category, sources, keywords):
        """Получает контент для определенной категории"""
        content_items = []
        
        for source in sources:
            feed = await self.fetch_rss_feed(source)
            if not feed or 'entries' not in feed:
                continue
            
            for entry in feed.entries:
                if not self.is_recent(entry):
                    continue
                
                # Проверяем, не публиковали ли уже
                if self.db.is_content_posted(entry.link):
                    continue
                
                # Проверяем по ключевым словам
                title = entry.title if hasattr(entry, 'title') else 'No title'
                summary = entry.summary if hasattr(entry, 'summary') else ''
                
                content_text = f"{title} {summary}"
                if self.matches_keywords(content_text, keywords):
                    # Парсим полный текст
                    full_content = self.parse_article_content(entry.link)
                    
                    content_items.append({
                        'title': title,
                        'url': entry.link,
                        'summary': summary,
                        'full_content': full_content,
                        'category': category
                    })
        
        return content_items