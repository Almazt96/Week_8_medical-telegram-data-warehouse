# Pydantic models
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# --- BASE RESPONSE CONFIGURATION ---
class SchemaBase(BaseModel):
    class Config:
        from_attributes = True  # Allows Pydantic to parse ORM/PostgreSQL objects directly


# --- DIMENSION STRUCTURE SCHEMAS ---
class ChannelDimension(SchemaBase):
    channel_key: str = Field(..., description="MD5 hash derived primary key identifying the channel")
    channel_name: str = Field(..., description="Public Telegram handle name")
    channel_type: str = Field(..., description="Categorized marketplace sector (e.g., Pharmaceutical, Cosmetics)")
    total_posts: int = Field(..., description="Cumulative message records ingested")
    avg_views: float = Field(..., description="Historical average viewer count per post")


class DateDimension(SchemaBase):
    date_key: int = Field(..., description="YYYYMMDD integer encoded key")
    full_date: date = Field(..., description="Standard calendar date timestamp")
    day_name: str = Field(..., description="Full day spelling (e.g., Monday)")
    is_weekend: bool = Field(..., description="Flag indicating if date falls on Saturday/Sunday")


# --- FACT STRUCTURE SCHEMAS ---
class MessageFact(SchemaBase):
    message_id: int = Field(..., description="Granular message trace identifier matching Telethon source logs")
    channel_key: str = Field(..., description="Surrogate key mapping back to dim_channels")
    date_key: int = Field(..., description="Surrogate date lookup key mapping to dim_dates")
    message_text: Optional[str] = Field(None, description="Raw text excerpt extracted from message post")
    view_count: int = Field(..., description="Total impression view count counter")
    forward_count: int = Field(..., description="Total message share forwarding metric tracking")
    has_image: bool = Field(..., description="Flag signaling linked object media assets in the raw storage bucket")


# --- ADVANCED ANALYTICAL PERFORMANCE RESPONSES ---
class ChannelRankingResponse(SchemaBase):
    channel_name: str
    channel_type: str
    total_engagements: int = Field(..., description="Combined sum of views and forward metrics")
    performance_tier: str = Field(..., description="Computed market velocity score based on engagement metrics")


class VisualDetectionResponse(SchemaBase):
    message_id: int
    channel_name: str
    detected_class: str = Field(..., description="ML classification extracted by YOLOv8 (e.g., bottle, pill packaging)")
    confidence_score: float = Field(..., description="Model accuracy confidence precision (0.0 to 1.0)")
    view_count: int


# --- ERROR SCHEMAS ---
class HTTPErrorDetail(BaseModel):
    detail: str = Field(..., description="Systemic tracking exception context message detailing failure root cause")