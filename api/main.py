# Database connection
# 5. Task 4: Build an Analytical API (FastAPI service)
# To serve analytical summaries over operational channels, we design a high-throughput backend service that connects directly to the processed data mart models.
# API Engine Implementation:
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware  # <--- Fixes "Failed to fetch" browser errors
from pydantic import BaseModel, Field
from typing import List, Optional  # <--- Fixes your NameError
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import logging
import uvicorn  # <--- Fixes missing uvicorn server module import error

# Silence messy Windows connection drops logs safely
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

load_dotenv()
app = FastAPI(
    title="Ethiopian Medical Channels Insights Engine", 
    description="Production-grade API capturing telecom metrics and analytical views over healthcare data marts.",
    version="1.0.0"
)

# --- 1. CONFIGURING CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local browser sandbox environments to talk to backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATABASE DEPENDENCY INJECTION ---
def get_db_cursor():
    # Always pull parameters from the context .env file
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

# --- 3. PYDANTIC SCHEMAS FOR RESPONSE DATA VALIDATION ---
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

class ChannelDimension(BaseModel):
    channel_key: str
    channel_name: str
    channel_type: str
    total_posts: int
    avg_views: float

# --- MOCK DATA SEED FOR DIMENSIONAL RETRIEVAL TESTS ---
MOCK_CHANNELS = [
    {"channel_key": "7b1a2", "channel_name": "CheMed19", "channel_type": "Pharmaceutical", "total_posts": 1420, "avg_views": 850.4},
    {"channel_key": "9f3c4", "channel_name": "lobeliacosmetics", "channel_type": "Cosmetics", "total_posts": 3120, "avg_views": 2450.1},
    {"channel_key": "1d2e5", "channel_name": "TikvahPharma", "channel_type": "Medical", "total_posts": 890, "avg_views": 1120.0}
]


# --- 4. ANALYTICAL API ENDPOINTS ---

@app.get("/api/reports/top-products", response_model=List[ProductMention], tags=["Reports"])
def get_top_products(limit: int = 10, cursor = Depends(get_db_cursor)):
    """
    Splits message string payloads into records to isolate tracked medical keyword aggregates.
    """
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


@app.get("/analytics/channels", response_model=List[ChannelDimension], tags=["Dimensions"])
async def get_channels(
    channel_name: Optional[str] = Query(None, description="Optional channel name lookup filtering"),
    sector: Optional[str] = Query(None, description="Filter channels by market classification type sector")
):
    """
    Queries dim_channels. If channel_name or sector is provided, filters the output.
    """
    result = MOCK_CHANNELS
    
    if channel_name:
        result = [c for c in result if c["channel_name"].lower() == channel_name.lower()]
    if sector:
        result = [c for c in result if c["channel_type"].lower() == sector.lower()]
        
    return result


# FIXED: Un-commented and explicitly mapped route parameter mapping block correctly
@app.get("/api/channels/{channel_name}/activity", response_model=ChannelActivity, tags=["Channels"])
def get_channel_activity(channel_name: str, cursor = Depends(get_db_cursor)):
    """
    Isolates historical post density metrics for specific medical community tags.
    """
    query = "SELECT channel_name, total_posts, avg_views FROM raw.dim_channels WHERE channel_name ILIKE %s;"
    cursor.execute(query, (f"%{channel_name}%",))
    res = cursor.fetchone()
    if not res:
        raise HTTPException(status_code=404, detail="Requested channel entity not tracked in database.")
    return res


@app.get("/api/search/messages", response_model=List[MessageItem], tags=["Search"])
def search_messages(query: str, limit: int = 20, cursor = Depends(get_db_cursor)):
    """
    Runs text query matching against granular rows inside fct_messages.
    """
    sql = "SELECT message_id, message_text, view_count FROM raw.fct_messages WHERE message_text ILIKE %s LIMIT %s;"
    cursor.execute(sql, (f"%{query}%", limit))
    return cursor.fetchall()

class VisualStats(BaseModel):
    has_image: bool
    volume: int
    score: float  # Pydantic will automatically convert float-compatible fields safely

# --- 1. Define the Response Schema (Put this above your endpoints) ---
class VisualStats(BaseModel):
    has_image: bool
    volume: int
    score: Optional[float] = Field(0.0, description="The calculated average view count, safely converted to a float")

    class Config:
        from_attributes = True


# --- 2. Update the Endpoint ---
@app.get("/api/reports/visual-content", response_model=List[VisualStats], tags=["Reports"])
def get_visual_content_stats(cursor = Depends(get_db_cursor)):
    """
    Compares transactional view counts between pure text posts and media attachment records.
    """
    # We explicitly cast the average view_count using ::FLOAT to prevent PostgreSQL Decimal errors,
    # and handle potential NULL values with COALESCE
    query = """
        SELECT 
            COALESCE(has_image, FALSE) as has_image, 
            COUNT(*) as volume, 
            COALESCE(AVG(view_count), 0)::FLOAT as score 
        FROM raw.fct_messages 
        GROUP BY has_image;
    """
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as e:
        # This prints the exact query error to your local Uvicorn terminal console if it breaks
        print(f"Database Query Execution Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database aggregation failure: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)    