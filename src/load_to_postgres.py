# Task 2: Data Modeling and Transformation (dbt)
# Data Base Loading Hook:
import os
import json
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def load_lake_to_postgres():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgress"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )
    cursor = conn.cursor()
    print("Successfully connected to PostgreSQL database!")
    
    # Initialize baseline schema
    cursor.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            message_id INT,
            channel_name VARCHAR(100),
            message_date TIMESTAMP,
            message_text TEXT,
            has_media BOOLEAN,
            image_path TEXT,
            views INT,
            forwards INT
        );
    """)
    conn.commit()

    # Discover and parse JSON data lake files
    base_dir = "data/raw/telegram_messages"
    if not os.path.exists(base_dir):
        print("Data lake path empty.")
        return

    all_records = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        all_records.append((
                            item['message_id'], item['channel_name'], item['message_date'],
                            item['message_text'], item['has_media'], item['image_path'],
                            item['views'], item['forwards']
                        ))

    # Clear prior sync batch to preserve idempotency
    cursor.execute("TRUNCATE TABLE raw.telegram_messages;")
    
    insert_query = """
        INSERT INTO raw.telegram_messages (message_id, channel_name, message_date, message_text, has_media, image_path, views, forwards)
        VALUES %s
    """
    execute_values(cursor, insert_query, all_records)
    conn.commit()
    print(f"Successfully processed and seeded {len(all_records)} messages into warehouse landing zone.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_lake_to_postgres()