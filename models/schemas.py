from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MentionedUser(BaseModel):
    """Individual mentioned user"""

    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    matched_term: Optional[str] = None
    display_name: Optional[str] = None


class UserInput(BaseModel):
    """User data from backend"""

    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class ProcessVideoRequest(BaseModel):
    """Request to process a video"""

    video_path: str = Field(..., description="Path to video file")
    video_id: str = Field(..., description="Unique video identifier")
    users: List[UserInput] = Field(
        ..., description="List of users for mention detection"
    )


class ProcessVideoResponse(BaseModel):
    """Response after processing video"""

    video_id: str
    mentioned_user_ids: List[int]
    mentioned_users: List[MentionedUser]
    mention_count: int
    transcript: str  # Backend saves this
    duration_seconds: float
    processed_at: str
    status: str = "success"


class TranscriptItem(BaseModel):
    """Single transcript for search"""

    video_id: str
    transcript: str


class SearchRequest(BaseModel):
    """Request to search transcripts"""

    query: str = Field(..., description="Search query")
    transcripts: List[TranscriptItem] = Field(
        ..., description="List of transcripts to search"
    )


class SearchResultItem(BaseModel):
    """Single search result"""

    video_id: str
    snippet: str
    match_count: int
    relevance_score: float


class SearchResponse(BaseModel):
    """Response from search"""

    query: str
    results: List[SearchResultItem]
    total_results: int


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    model_loaded: bool
    version: str = "1.0.0"
