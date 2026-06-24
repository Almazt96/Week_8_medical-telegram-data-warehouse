# Week_8_medical-telegram-data-warehouse
A guide to implementing Telegram scraping using Telethon and setting up an immutable, partitioned Data Lake directory design.

Part 1: Data Lake Architecture & Directory Design
In a modern ELT (Extract, Load, Transform) pipeline, the raw landing zone must be immutable and chronologically partitioned. This ensures that if downstream transformations fail, the source data can be re-processed without losing history or re-scraping the API (which risks rate-limiting blocks).

For our Telegram medical data platform, the data lake stores text/metadata as partitioned JSON blobs and downloads corresponding product binary media into distinct folder structures:

Plaintext
data_lake/
└── raw/
    ├── telegram_messages/                 # Text & Metadata Zone (Partitioned by Ingestion Date)
    │   ├── 2026-06-24/
    │   │   ├── CheMed19.json              # Raw, unstructured JSON payload from @CheMed19
    │   │   ├── lobeliacosmetics.json      # Raw payload from @lobeliacosmetics
    │   │   └── TikvahPharma.json          # Raw payload from @TikvahPharma
    │   └── 2026-06-25/
    │       └── ...
    └── images/                            # Raw Binary Media Zone (Segregated by Source Handle)
        ├── CheMed19/
        │   ├── 1042.jpg                   # Downloaded visual attachment matching message_id
        │   └── 1043.jpg
        └── lobeliacosmetics/
            └── 2150.jpg
Part 2: Implementation — Telethon Scraper & Lake Exporter
This asynchronous Python script authenticates with the Telegram API using Telethon, iterates through the targeted channels, extracts core fields (message text, IDs, view counts, forwards), automatically downloads media to the binary zone, and flushes the date-partitioned JSON to the metadata zone.

1. Setup Configuration (.env)
Create a .env file to hold your secret Telegram credentials safely (you can obtain these from my.telegram.org):

Code snippet
TG_API_ID=12345678
TG_API_HASH=abcdef0123456789abcdef0123456789
2. Python Production Script (scraper.py)
Python
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient

# Load Environment Variables
load_dotenv()

# Setup Structured Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/scraper_{datetime.utcnow().strftime('%Y%m%d')}.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")
TARGET_CHANNELS = ["@CheMed19", "@lobeliacosmetics", "@TikvahPharma"]

async def scrape_channel_to_lake(client, channel_username):
    logging.info(f"Initiating extraction loop for target: {channel_username}")
    print(f"Scraping channel: {channel_username}...")
    
    try:
        entity = await client.get_entity(channel_username)
        messages_data = []
        
        # Resolve Data Lake Partition Paths
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        json_partition_dir = f"data_lake/raw/telegram_messages/{today_str}"
        image_store_dir = f"data_lake/raw/images/{channel_username.strip('@')}"
        
        os.makedirs(json_partition_dir, exist_ok=True)
        os.makedirs(image_store_dir, exist_ok=True)

        # Iterate through the latest 100 posts
        async for msg in client.iter_messages(entity, limit=100):
            msg_id = msg.id
            has_media = msg.photo is not None
            downloaded_image_path = None

            # Handle Binary Extraction if an image attachment exists
            if has_media:
                filename = f"{msg_id}.jpg"
                destination_path = os.path.join(image_store_dir, filename)
                
                # Asynchronously download media directly to the lake zone
                await client.download_media(msg.photo, file=destination_path)
                downloaded_image_path = destination_path
                logging.info(f"Downloaded image attachment for message_id {msg_id}")

            # Construct Schema-Agnostic Raw Document Payload
            record = {
                "message_id": msg_id,
                "channel_handle": channel_username,
                "extracted_at": datetime.utcnow().isoformat(),
                "message_date": msg.date.isoformat() if msg.date else None,
                "message_text": msg.text or "",
                "has_media": has_media,
                "image_path": downloaded_image_path,
                "views_count": msg.views or 0,
                "forwards_count": msg.forwards or 0
            }
            messages_data.append(record)

        # Write immutable JSON collection block into date-partitioned folder
        output_file_path = os.path.join(json_partition_dir, f"{channel_username.strip('@')}.json")
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(messages_data, f, indent=4, ensure_ascii=False)
            
        logging.info(f"Finished channel {channel_username}. Written {len(messages_data)} records to data lake partition.")
        print(f"Successfully saved {len(messages_data)} records for {channel_username}.")
        
    except Exception as e:
        logging.error(f"Critical operational breakdown during extraction from {channel_username}: {str(e)}")
        print(f"Error scraping {channel_username}: {e}")

async def main():
    # Initialize session client ('session_scout' creates a local storage .session token file)
    async with TelegramClient('session_scout', int(API_ID), API_HASH) as client:
        for channel in TARGET_CHANNELS:
            await scrape_channel_to_lake(client, channel)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
Part 3: Operational Checklist for Production Data Pipelines
Session Handling: When you run the script for the first time, Telethon will prompt you to type in your phone number and the verification code sent to your Telegram app. It securely stores a session_scout.session file locally. Keep this safe and do not upload it to Git.

Handling Telegram API Flood Limits: If scraping hundreds of channels over broad histories, wrap your requests inside random sleep backoffs (asyncio.sleep(3)) to emulate realistic programmatic behaviors and prevent FloodWaitError warnings.

Downstream Consumption: Your dbt transformation or raw staging loaders can run a daily cron process scanning data_lake/raw/telegram_messages/{YYYY-MM-DD}/*.json to instantly parse and stage fresh data points into the data warehouse.