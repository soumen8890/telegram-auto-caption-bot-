
# Auto Caption Bot for Telegram Channels

Automatically adds formatted captions to media files posted in Telegram channels.

## Features

- Supports all standard media variables
- Automatic metadata extraction
- Customizable caption templates
- Easy deployment

## Variables Available

- `{filename}` - File name
- `{filesize}` - File size
- `{caption}` - Original caption
- `{language}` - Language from filename
- `{year}` - Year from filename
- `{quality}` - Quality from filename
- `{season}` - Season from filename
- `{episode}` - Episode from filename
- `{duration}` - Duration from video
- `{height}` - Video height
- `{width}` - Video width
- `{ext}` - File extension
- `{resolution}` - Video resolution
- `{mime_type}` - MIME type
- `{title}` - Audio title
- `{artist}` - Audio artist
- `{wish}` - Time-based greeting

## Deployment

1. Create a new Web Service on Render
2. Set environment variables from `.env.sample`
3. Deploy!
