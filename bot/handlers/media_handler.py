
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.utils import caption_generator
from bot.database import crud

async def handle_single_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    message = update.message
    chat_id = message.chat.id
    
    # Get channel's caption template
    template = await crud.get_channel_template(chat_id)
    if not template:
        return
    
    # Generate new caption
    new_caption = await caption_generator.generate_caption(
        message=message,
        template=template
    )
    
    # Edit the message caption
    if new_caption:
        await message.edit_caption(new_caption)

async def handle_media_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.media_group_id:
        return
    
    # Similar logic as single media but for groups
    # Implementation would handle all media in group

# Handlers
single_media_handler = MessageHandler(
    filters.CAPTION | filters.PHOTO | filters.VIDEO | filters.DOCUMENT,
    handle_single_media
)

media_group_handler = MessageHandler(
    filters.MEDIA_GROUP,
    handle_media_group
)
