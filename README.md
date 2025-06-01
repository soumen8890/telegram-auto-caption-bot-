# Telegram Auto Caption Bot

Advanced auto caption bot for Telegram channels with support for dynamic variables.

## Features

- Automatic caption generation for media files
- Support for all common media types (photos, videos, documents, audio)
- 20+ dynamic variables including:
  - File metadata (`{filename}`, `{filesize}`, `{ext}`)
  - Media info (`{duration}`, `{resolution}`, `{mime_type}`)
  - Audio tags (`{title}`, `{artist}`)
  - Time-based wishes (`{wish}`)
  - File name patterns (`{language}`, `{year}`, `{quality}`)

## Setup

1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Create `.env` file from `.env.example`
4. Run the bot: `python -m bot.main`

## Usage

1. Add bot to your channel as admin with "Edit Messages" permission
2. Set your caption template with `/setcaption`
3. The bot will automatically update all media captions

## Variables

All available variables are listed in [VARIABLES.md](VARIABLES.md)-
