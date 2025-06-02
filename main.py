
import os
import re
import datetime
import tempfile
from typing import Dict, Optional
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    Defaults
)
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pymediainfo import MediaInfo
from jinja2 import Environment, FileSystemLoader

# Load environment variables
load_dotenv()

class AutoCaptionBot:
    def __init__(self):
        self.token = os.getenv("BOT_TOKEN")
        self.template_name = os.getenv("TEMPLATE_NAME", "default.html")
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
        # Set up bot with HTML defaults
        defaults = Defaults(
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        self.updater = Updater(
            token=self.token,
            defaults=defaults,
            use_context=True
        )
        
        # Add handlers
        self.updater.dispatcher.add_handler(
            MessageHandler(
                Filters.document | Filters.video | Filters.audio | Filters.photo,
                self.handle_media
            )
        )
        
    def start(self):
        print("Bot is running with HTML support...")
        self.updater.start_polling()
        self.updater.idle()
        
    def handle_media(self, update: Update, context: CallbackContext):
        message = update.effective_message
        if not message:
            return
            
        try:
            # Get basic file info
            file = (message.document or message.video or 
                   message.audio or message.photo[-1] if message.photo else None)
            if not file:
                return
                
            filename = file.file_name or ""
            filesize = self._human_readable_size(file.file_size)
            ext = os.path.splitext(filename)[1][1:].upper() if file.file_name else ""
            
            # Parse filename for metadata
            parsed_info = self._parse_filename(filename)
            
            # Get media info
            media_info = self._get_media_info(file)
            
            # Get wish based on current time
            wish = self._get_wish()
            
            # Prepare all variables
            variables = {
                "filename": filename,
                "filesize": filesize,
                "original_caption": message.caption or "",
                "language": parsed_info.get("language", ""),
                "year": parsed_info.get("year", ""),
                "quality": parsed_info.get("quality", ""),
                "season": parsed_info.get("season", ""),
                "episode": parsed_info.get("episode", ""),
                "duration": media_info.get("duration", ""),
                "height": media_info.get("height", ""),
                "width": media_info.get("width", ""),
                "ext": ext,
                "resolution": media_info.get("resolution", ""),
                "mime_type": file.mime_type,
                "title": media_info.get("title", ""),
                "artist": media_info.get("artist", ""),
                "wish": wish,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Render HTML caption
            template = self.env.get_template(self.template_name)
            caption = template.render(**variables)
            
            # Edit message with new caption
            try:
                if message.caption:
                    message.edit_caption(caption=caption, parse_mode="HTML")
                else:
                    # For photos without caption
                    if message.photo:
                        message.edit_caption(caption=caption, parse_mode="HTML")
            except Exception as e:
                print(f"Error editing caption: {e}")
                
        except Exception as e:
            print(f"Error processing message: {e}")

    # ... [keep all the helper methods from previous version] ...

if __name__ == "__main__":
    bot = AutoCaptionBot()
    bot.start()
