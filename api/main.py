# FastAPI application
# 5. Task 4: Build an Analytical API (FastAPI service)
# To serve analytical summaries over operational channels, we design a high-throughput backend service that connects directly to the processed data mart models.
# API Engine Implementation:
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Ethiopian Medical Channels Insights Engine", version="1.0.0")

def get_db_cursor():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=RealDictCursor
    )
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()

class ProductMention(BaseModel):
    product_name: str
    mention_count: int

class ChannelActivity(BaseModel):
    channel_name: str
    total_posts: int
    avg_views: float

class MessageItem(BaseModel):
    message_id: int
    message_text: str
    view_count: int

@app.get("/api/reports/top-products", response_model=List[ProductMention])
def get_top_products(limit: int = 10, cursor = Depends(get_db_cursor)):
    query = r"""
        SELECT word as product_name, count(*) as mention_count 
        FROM (
            SELECT regexp_split_to_table(lower(message_text), '\s+') as word 
            FROM raw.telegram_messages
        ) w 
        WHERE length(word) > 4 AND word IN ('paracetamol', 'amoxicillin', 'vitamin', 'cream', 'serum', 'insulin')
        GROUP BY word ORDER BY mention_count DESC LIMIT %s;
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()

@app.get("/api/channels/{channel_name}/activity", response_model=ChannelActivity)
def get_channel_activity(channel_name: str, cursor = Depends(get_db_cursor)):
    query = "SELECT channel_name, total_posts, avg_views FROM dim_channels WHERE channel_name ILIKE %s;"
    cursor.execute(query, (f"%{channel_name}%",))
    res = cursor.fetchone()
    if not res:
        raise HTTPException(status_code=404, detail="Requested channel entity not tracked.")
    return res

@app.get("/api/search/messages", response_model=List[MessageItem])
def search_messages(query: str, limit: int = 20, cursor = Depends(get_db_cursor)):
    sql = "SELECT message_id, message_text, view_count FROM fct_messages WHERE message_text ILIKE %s LIMIT %s;"
    cursor.execute(sql, (f"%{query}%", limit))
    return cursor.fetchall()

@app.get("/api/reports/visual-content")
def get_visual_content_stats(cursor = Depends(get_db_cursor)):
    query = "SELECT has_image, count(*) as volume, avg(view_count) as score FROM fct_messages GROUP BY has_image;"
    cursor.execute(query)
    return cursor.fetchall()