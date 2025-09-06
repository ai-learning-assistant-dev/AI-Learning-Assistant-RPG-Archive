"""
Pydantic schemas for request and response models.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.card import CharacterCardV3


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


class CraftCardResponse(BaseModel):
    card: CharacterCardV3 | None = None
