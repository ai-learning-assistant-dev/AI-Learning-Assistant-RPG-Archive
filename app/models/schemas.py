"""
Pydantic schemas for request and response models.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    msg: str
    detail: Optional[str] = None


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ChatRequest(BaseModel):
    message: str
