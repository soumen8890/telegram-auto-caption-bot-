# main.py
import os
import re
import logging
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import Update, InputFile
from telegram.ext import (
    Updater, CommandHandler,
    MessageHandler, Filters,
    CallbackContext, Defaults
)
from pyrogram import Client
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pymediainfo import MediaInfo
from jinja2 import Environment, FileSystemLoader

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AutoCaptionBot:
    def __init__(self):
        # Telegram API credentials
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.bot_token = os.getenv("BOT_TOKEN")
        self.owner_id = int(os.getenv("OWNER_ID", 0))
        
        # MongoDB configuration
        self.mongo_uri = os.getenv("MONGO_URI")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['AutoCaptionBot']
        self.channels = self.db['channels']
        self.templates = self.db['templates']
        
        # Initialize Pyrogram client for advanced media handling
        self.pyro_client = Client(
            "auto_caption_session",
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=self.bot_token
        )
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
        # Telegram bot defaults
        defaults = Defaults(
            parse_mode="HTML",
            disable_web_page_preview=True,
            quote=True
        )
        
        self.updater = Updater(
            token=self.bot_token,
            defaults=defaults,
            use_context=True
        )
        
        # Register handlers
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start_cmd))
        dp.add_handler(CommandHandler("addchannel", self.add_channel))
        dp.add_handler(CommandHandler("settemplate", self.set_template))
        dp.add_handler(MessageHandler(
            Filters.document | Filters.video | Filters.audio | Filters.photo,
            self.handle_media
        ))
        
    def start(self):
        """Start the bot services"""
        self.pyro_client.start()
        self.updater.start_polling()
        logger.info("Bot started successfully")
        self.updater.idle()
        
    async def start_cmd(self, update: Update, context: CallbackContext):
        """Start command handler"""
        if update.effective_user.id != self.owner_id:
            update.message.reply_text("⚠️ You're not authorized!")
            return
            
        await update.message.reply_html(
            "⚡ <b>Auto Caption Bot</b> ⚡\n\n"
            "📌 <code>/addchannel</code> - Add a channel\n"
            "📌 <code>/settemplate</code> - Set HTML template\n"
            "📌 Just forward media to test"
        )
        
    async def add_channel(self, update: Update, context: CallbackContext):
        """Add channel to database"""
        if update.effective_user.id != self.owner_id:
            return
            
        try:
            channel_id = update.message.forward_from_chat.id
            self.channels.insert_one({
                "channel_id": channel_id,
                "template": "default.html",
                "added_at": datetime.now()
            })
            await update.message.reply_text(f"✅ Channel {channel_id} added!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
    async def set_template(self, update: Update, context: CallbackContext):
        """Set template for a channel"""
        if update.effective_user.id != self.owner_id:
            return
            
        try:
            args = context.args
            if len(args) < 2:
                await update.message.reply_text("Usage: /settemplate <channel_id> <template_name>")
                return
                
            channel_id = int(args[0])
            template_name = args[1]
            
            self.channels.update_one(
                {"channel_id": channel_id},
                {"$set": {"template": template_name}}
            )
            await update.message.reply_text("✅ Template updated!")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
            
    async def handle_media(self, update: Update, context: CallbackContext):
        """Process media and apply captions"""
        try:
            message = update.effective_message
            if not message:
                return
                
            # Check if from authorized channel
            channel = self.channels.find_one({"channel_id": message.chat.id})
            if not channel:
                return
                
            # Get media file
            file = (message.document or message.video or 
                   message.audio or message.photo[-1] if message.photo else None)
            if not file:
                return
                
            # Extract metadata
            metadata = await self.extract_metadata(file)
            
            # Get template
            template = self.templates.find_one({"name": channel['template']}) or {}
            html_content = template.get("content", self.get_default_template())
            
            # Render caption
            caption = self.env.from_string(html_content).render(
                **metadata,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Apply caption
            await message.edit_caption(
                caption=caption,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Error processing media: {str(e)}")
            
    async def extract_metadata(self, file) -> Dict:
        """Extract metadata from media file"""
        metadata = {
            "filename": file.file_name or "",
            "filesize": self.human_readable_size(file.file_size),
            "mime_type": file.mime_type,
            "original_caption": getattr(file, 'caption', "")
        }
        
        # Download and analyze file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_path = temp_file.name
            await file.download_to_drive(file_path)
            
            try:
                # Hachoir metadata
                parser = createParser(file_path)
                if parser:
                    hachoir_meta = extractMetadata(parser)
                    if hachoir_meta:
                        if hachoir_meta.has("duration"):
                            seconds = hachoir_meta.get("duration").seconds
                            metadata["duration"] = f"{seconds//3600:02d}:{(seconds%3600)//60:02d}:{seconds%60:02d}"
                        if hachoir_meta.has("width"):
                            metadata["width"] = hachoir_meta.get("width")
                        if hachoir_meta.has("height"):
                            metadata["height"] = hachoir_meta.get("height")
                            
                # MediaInfo metadata
                media_info = MediaInfo.parse(file_path)
                for track in media_info.tracks:
                    if track.track_type == "Video":
                        metadata.update({
                            "resolution": f"{track.width}x{track.height}",
                            "quality": self.determine_quality(track.width, track.height)
                        })
                    elif track.track_type == "Audio":
                        metadata.update({
                            "title": getattr(track, "title", ""),
                            "artist": getattr(track, "performer", "")
                        })
                    
                # Filename parsing
                if file.file_name:
                    parsed = self.parse_filename(file.file_name)
                    metadata.update(parsed)
                    
            finally:
                os.unlink(file_path)
                
        return metadata
        
    def get_default_template(self):
        """Fallback template"""
        return """
<b>{{ filename }}</b>
<code>
📁 {{ filesize }} | 🕒 {{ duration }}
🎞️ {{ resolution }} ({{ quality }})
{% if year %}🗓️ {{ year }}{% endif %}
{% if language %} | 🌍 {{ language }}{% endif %}
</code>
{% if original_caption %}
<i>{{ original_caption }}</i>
{% endif %}
"""
        
    # Helper methods...
    def human_readable_size(self, size_bytes):
        """Convert bytes to human readable format"""
        # ... (same as previous implementation)
        
    def parse_filename(self, filename):
        """Extract metadata from filename"""
        # ... (same as previous implementation)
        
    def determine_quality(self, width, height):
        """Determine quality from resolution"""
        if height >= 2160 or width >= 3840:
            return "4K"
        elif height >= 1080:
            return "FHD"
        elif height >= 720:
            return "HD"
        return "SD"

if __name__ == "__main__":
    bot = AutoCaptionBot()
    bot.start()
