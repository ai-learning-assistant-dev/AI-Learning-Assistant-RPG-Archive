"""
Pydantic schemas for request and response models.
"""

from datetime import datetime
from typing import Any, Callable, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from .store import Session

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T, code: int = 200, message: str = "success"):
        return cls(code=code, message=message, data=data)

    @classmethod
    def error(cls, data: T, code: int = 400, message: str = "error"):
        return cls(code=code, message=message, data=data)


def standard_response():
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs) -> BaseResponse[Any]:
            try:
                result = await func(*args, **kwargs)
                return BaseResponse.success(data=result)
            except Exception as e:
                raise e  # 交给全局异常处理器处理

        return wrapper

    return decorator


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class CraftCardRequest(BaseModel):
    query: str = Field(..., description="The query to describe card")
    session_id: str = Field(..., description="The session ID")
    parent_cid: str = Field(default="", description="Parent conversation ID")
    model: str = Field(default="default", description="The model to use")


class StreamEvent(BaseModel):

    session_id: str = Field(..., description="Session ID")
    conversation_id: str = Field(..., description="Conversation ID")
    parent_id: str = Field(default="", description="Parent conversation ID")
    data: dict[str, Any] = Field(default_factory=dict, description="Event data")


class SessionListRequest(BaseModel):
    limit: int = Field(50, gt=0, le=100, description="Number of sessions to return")
    offset: int = Field(0, ge=0, description="Number of sessions to skip")


class SessionListResponse(BaseModel):
    sessions: list[Session] = Field(default=[], description="List of sessions")


class ConversationListRequest(BaseModel):
    session_id: str = Field(..., description="The session ID to list conversations for")


class ConversationListResponse(BaseModel):
    conversations: list[str] = Field(default=[], description="List of conversations")
