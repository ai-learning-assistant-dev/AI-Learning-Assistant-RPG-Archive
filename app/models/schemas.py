"""
Pydantic schemas for request and response models.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    msg: str
    detail: str | None = None


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class CraftCardRequest(BaseModel):
    query: str = Field(..., description="The query to describe card")


class StreamEvent(BaseModel):
    session_id: str = Field(..., description="Session ID")
    conversation_id: str = Field(..., description="Conversation ID")
    parent_id: str = Field(default="", description="Parent conversation ID")
