async def main():
    async with telethon.TelegramClient('session_scout', int(API_ID), API_HASH) as client:
        print("Testing connection...")
        
        # Fetch the 5 most recent chats you have open
        async for dialog in client.iter_dialogs(limit=5):
            print(f"Connected successfully to chat: {dialog.name} (ID: {dialog.id})")

if __name__ == "__main__":
    asyncio.run(main())