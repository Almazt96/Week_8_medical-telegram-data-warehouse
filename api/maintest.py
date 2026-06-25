import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

async def main():
    async with TelegramClient('session_scout', int(API_ID), API_HASH) as client:
        print("Testing connection...")
        
        # Fetch the 5 most recent chats you have open
        async for dialog in client.iter_dialogs(limit=5):
            print(f"Connected successfully to chat: {dialog.name} (ID: {dialog.id})")

if __name__ == "__main__":
    asyncio.run(main())