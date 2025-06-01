
import logging
from telegram.ext import Application
from dotenv import load_dotenv
import os

from bot.handlers import command_handler, media_handler
from config import Config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=Config.LOG_LEVEL
)

async def post_init(application: Application):
    await application.bot.set_my_commands([
        ('start', 'Start the bot'),
        ('setcaption', 'Set custom caption template'),
        ('variables', 'Show available variables')
    ])

def main():
    load_dotenv()
    application = Application.builder().token(Config.BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(command_handler.start_handler)
    application.add_handler(command_handler.set_caption_handler)
    application.add_handler(command_handler.variables_handler)
    application.add_handler(media_handler.media_group_handler)
    application.add_handler(media_handler.single_media_handler)
    
    application.run_polling()

if __name__ == '__main__':
    main()
