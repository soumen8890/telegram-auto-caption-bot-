
import re
from datetime import datetime
from typing import Optional
from telegram import Message
from bot.utils.file_parser import parse_filename
from bot.utils.helpers import sizeof_fmt, get_time_based_wish

class CaptionGenerator:
    @staticmethod
    async def generate_caption(message: Message, template: str) -> Optional[str]:
        file_meta = await CaptionGenerator._get_file_metadata(message)
        variables = await CaptionGenerator._prepare_variables(message, file_meta)
        
        try:
            return template.format(**variables)
        except KeyError as e:
            logging.error(f"Missing variable in template: {e}")
            return None

    @staticmethod
    async def _get_file_metadata(message: Message) -> dict:
        """Extract metadata from the message and file"""
        file = (message.document or message.video or message.audio or message.photo[-1] if message.photo else None)
        if not file:
            return {}
        
        file_name = getattr(file, 'file_name', '')
        return {
            **parse_filename(file_name),
            'mime_type': getattr(file, 'mime_type', ''),
            'duration': getattr(file, 'duration', 0),
            'width': getattr(file, 'width', 0),
            'height': getattr(file, 'height', 0),
            'title': getattr(file, 'title', ''),
            'performer': getattr(file, 'performer', '')
        }

    @staticmethod
    async def _prepare_variables(message: Message, file_meta: dict) -> dict:
        """Prepare all available variables for caption"""
        file = (message.document or message.video or message.audio or message.photo[-1] if message.photo else None)
        
        return {
            'filename': file_meta.get('filename', ''),
            'filesize': sizeof_fmt(getattr(file, 'file_size', 0)),
            'caption': message.caption or '',
            'language': file_meta.get('language', ''),
            'year': file_meta.get('year', ''),
            'quality': file_meta.get('quality', ''),
            'season': file_meta.get('season', ''),
            'episode': file_meta.get('episode', ''),
            'ext': file_meta.get('ext', ''),
            'mime_type': file_meta.get('mime_type', ''),
            'title': file_meta.get('title', ''),
            'artist': file_meta.get('performer', ''),
            'wish': get_time_based_wish(),
            'duration': str(datetime.timedelta(seconds=file_meta.get('duration', 0))),
            'height': str(file_meta.get('height', 0)),
            'width': str(file_meta.get('width', 0)),
            'resolution': f"{file_meta.get('width', 0)}x{file_meta.get('height', 0)}"
        }
