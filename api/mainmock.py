# FastAPI application
from fastapi import FastAPI, HTTPException, Query, status
from typing import List, Optional  # <--- Fixes your previous NameError
import uvicorn

# Import localized components
try:
    from api.schemas import ChannelDimension, MessageFact, ChannelRankingResponse, VisualDetectionResponse, HTTPErrorDetail
except ImportError:
    from schemas import ChannelDimension, MessageFact, ChannelRankingResponse, VisualDetectionResponse, HTTPErrorDetail

app = FastAPI(
    title="Kara Solutions — Medical Intelligence Engine Analytical API",
    version="1.0.0"
)

# --- CORRECTED MOCK DATA ---
MOCK_CHANNELS = [
    {"channel_key": "7b1a2", "channel_name": "CheMed19", "channel_type": "Pharmaceutical", "total_posts": 1420, "avg_views": 850.4},
    {"channel_key": "9f3c4", "channel_name": "lobeliacosmetics", "channel_type": "Cosmetics", "total_posts": 3120, "avg_views": 2450.1},
    {"channel_key": "1d2e5", "channel_name": "TikvahPharma", "channel_type": "Medical", "total_posts": 890, "avg_views": 1120.0}
]

MOCK_RANKINGS = [
    {"channel_name": "lobeliacosmetics", "channel_type": "Cosmetics", "total_engagements": 78000, "performance_tier": "High Alpha"},
    {"channel_name": "TikvahPharma", "channel_type": "Medical", "total_engagements": 22000, "performance_tier": "Stable Beta"},
    {"channel_name": "CheMed19", "channel_type": "Pharmaceutical", "total_engagements": 14500, "performance_tier": "Emerging"}
]

MOCK_DETECTIONS = [
    {
        "message_id": 1042, 
        "channel_name": "lobeliacosmetics", 
        "detected_class": "bottle", 
        "confidence_score": 0.91, 
        "view_count": 3100
    },
    {
        "message_id": 1045,  # <--- ADDED THIS FIELD TO FIX THE VALIDATION ERROR
        "channel_name": "CheMed19", 
        "detected_class": "pill packaging", 
        "confidence_score": 0.86, 
        "view_count": 920
    }
]

# --- ENDPOINTS ---
@app.get("/analytics/channels", response_model=List[ChannelDimension], tags=["Dimensions"])
async def get_channels(sector: Optional[str] = None):
    if sector:
        filtered = [c for c in MOCK_CHANNELS if c["channel_type"].lower() == sector.lower()]
        return filtered
    return MOCK_CHANNELS

@app.get("/analytics/rankings", response_model=List[ChannelRankingResponse], tags=["Metrics"])
async def get_channel_leaderboard(min_engagement: int = 0):
    return [r for r in MOCK_RANKINGS if r["total_engagements"] >= min_engagement]

@app.get("/analytics/vision-detections", response_model=List[VisualDetectionResponse], tags=["Inference"])
async def get_vision_inferences(target_class: Optional[str] = None):
    if target_class:
        return [d for d in MOCK_DETECTIONS if d["detected_class"].lower() == target_class.lower()]
    return MOCK_DETECTIONS

@app.get("/analytics/message/{message_id}", response_model=MessageFact, tags=["Facts"])
async def get_message_by_id(message_id: int):
    if message_id == 1042:
        return {
            "message_id": 1042, "channel_key": "9f3c4", "date_key": 20260624,
            "message_text": "Premium clinical treatment serum in stock.",
            "view_count": 3100, "forward_count": 42, "has_image": True
        }
    raise HTTPException(status_code=404, detail="Message record not found.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)