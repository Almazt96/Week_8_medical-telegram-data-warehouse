# Task_1: Script Implementation: src/scraper.py
# This production script uses Telethon to process groups 
# asynchronously, manages session instances securely, 
# and implements directory partitioning.
# Telethon extractor
import os
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
import asyncio

# Force python-dotenv to look at the project root directory
# This finds the .env file even if you execute the script from a subfolder
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path)

# Retrieve the variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
# API_ID = os.getenv("TG_API_ID")
# API_HASH = os.getenv("TG_API_HASH")
CHANNELS = ["@CheMed123", "@lobelia4cosmetics", "@tikvahpharma","@TGStat"]

# Quick safety check to prevent the crash and tell you exactly what's missing
if not API_ID or not API_HASH:
    raise ValueError(f"Failed to load API credentials. Check your .env file at: {dotenv_path}")

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(

    filename=f"logs/scraper_{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

async def scrape_channel(client, channel_username):
    logging.info(f"Starting scraping for channel: {channel_username}")
    try:
        entity = await client.get_entity(channel_username)
        messages_data = []
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Target data folder structure
        json_dir = f"data/raw/telegram_messages/{today_str}"
        img_dir = f"data/raw/images/{channel_username.strip('@')}"
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)

        async for msg in client.iter_messages(entity, limit=100):
            msg_id = msg.id
            has_media = msg.photo is not None
            image_path = None

            if has_media:
                filename = f"{msg_id}.jpg"
                path = os.path.join(img_dir, filename)
                await client.download_media(msg.photo, file=path)
                image_path = path
                logging.info(f"Downloaded media for message {msg_id}")

            record = {
                "message_id": msg_id,
                "channel_name": channel_username,
                "message_date": msg.date.isoformat() if msg.date else None,
                "message_text": msg.text or "",
                "has_media": has_media,
                "image_path": image_path,
                "views": msg.views or 0,
                "forwards": msg.forwards or 0
            }
            messages_data.append(record)

        # Write to partitioned data lake zone
        output_file = os.path.join(json_dir, f"{channel_username.strip('@')}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, indent=4, ensure_ascii=False)
            
        logging.info(f"Completed channel {channel_username}. Saved {len(messages_data)} records.")
    except Exception as e:
        logging.error(f"Error extracting from {channel_username}: {str(e)}")

async def main():
    # Your existing code setup...
    async with TelegramClient('session_scout', int(API_ID), API_HASH) as client:
        for channel in CHANNELS:
            await scrape_channel(client, channel)
        pass

if __name__ == "__main__":
    asyncio.run(main())