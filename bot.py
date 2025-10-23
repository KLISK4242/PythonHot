import logging
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import asyncio
from datetime import datetime
import time

from config import Config
from database import Database
from content_parsers import ContentParser

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EducationalBot:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.parser = ContentParser(self.db)
        self.app = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("find_content", self.find_content))
        self.app.add_handler(CommandHandler("stats", self.stats))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "🤖 Образовательный бот\n\n"
            "Команды:\n"
            "/find_content - Найти новый контент\n"
            "/stats - Статистика\n\n"
            "Бот автоматически ищет контент по IT, языкам и истории."
        )
    
    async def find_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ручной поиск контента"""
        await update.message.reply_text("🔍 Ищу новый контент...")
        
        found_count = await self.collect_and_send_content()
        
        await update.message.reply_text(f"✅ Найдено и отправлено {found_count} материалов")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика бота"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) FROM posted_content 
            GROUP BY category
        ''')
        stats = cursor.fetchall()
        
        message = "📊 Статистика бота:\n\n"
        for category, count in stats:
            message += f"{category}: {count} материалов\n"
        
        await update.message.reply_text(message)
    
    async def collect_and_send_content(self):
        """Сбор и отправка контента"""
        total_found = 0
        
        for category, sources in self.config.CONTENT_SOURCES.items():
            keywords = self.config.KEYWORDS.get(category, [])
            
            content_items = await self.parser.get_content_for_category(
                category, sources, keywords
            )
            
            for item in content_items:
                try:
                    await self.send_to_channel(item)
                    self.db.mark_as_posted(
                        item['title'], 
                        item['url'], 
                        item['category']
                    )
                    total_found += 1
                    
                    # Пауза между отправками
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error sending content: {e}")
        
        return total_found
    
    async def send_to_channel(self, content_item):
        """Отправка контента в канал"""
        category_emojis = {
            'programming': '💻',
            'languages': '🌍', 
            'history': '📚'
        }
        
        emoji = category_emojis.get(content_item['category'], '📖')
        
        message = f"{emoji} <b>{content_item['title']}</b>\n\n"
        
        if content_item['full_content']:
            message += f"{content_item['full_content']}\n\n"
        elif content_item['summary']:
            message += f"{content_item['summary']}\n\n"
        
        message += f"🔗 <a href='{content_item['url']}'>Читать полностью</a>\n"
        message += f"🏷️ #{content_item['category']}"
        
        await self.app.bot.send_message(
            chat_id=self.config.CHANNEL_ID,
            text=message,
            parse_mode='HTML',
            disable_web_page_preview=False
        )
    
    async def auto_post_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Автоматическая отправка контента по расписанию"""
        logger.info("🔄 Запуск автоматического поиска контента")
        
        try:
            found_count = await self.collect_and_send_content()
            logger.info(f"✅ Автоматически отправлено {found_count} материалов")
        except Exception as e:
            logger.error(f"❌ Ошибка в auto_post_job: {e}")
    
    def run(self):
        """Запуск бота"""
        # Добавляем задание по расписанию (каждые 6 часов)
        job_queue = self.app.job_queue
        job_queue.run_repeating(
            self.auto_post_job,
            interval=21600,  # 6 часов в секундах
            first=10
        )
        
        logger.info("🤖 Бот запущен!")
        self.app.run_polling()

if __name__ == '__main__':
    bot = EducationalBot()
    bot.run()