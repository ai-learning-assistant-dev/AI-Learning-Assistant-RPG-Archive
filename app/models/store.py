from enum import Enum

from pydantic import BaseModel, Field


class SessionType(str, Enum):
    CHAT = "chat"
    CRAFTCARD = "craftcard"
    OTHER = "other"


class ConversationType(str, Enum):
    HUMAN = "human"
    AI = "ai"


class Session(BaseModel):
    id: str = Field(..., description="Unique identifier for the session")
    title: str = Field(..., description="Title of the session")
    type: str = Field(..., description="Type of the session")
    created_at: str = Field(
        ..., description="ISO timestamp when the session was created"
    )


class Conversation(BaseModel):
    id: str = Field(..., description="Unique identifier for the conversation")
    session_id: str = Field(
        ..., description="Identifier of the session this conversation belongs to"
    )
    content: str = Field(..., description="Content of the conversation")
    type: str = Field(..., description="Type of the conversation")
    created_at: str = Field(
        ..., description="ISO timestamp when the conversation was created"
    )


class Card(BaseModel):
    """Model for storing card data."""

    id: str = Field(..., description="Unique identifier for the card")
    session_id: str = Field(
        ..., description="Identifier of the session this card belongs to"
    )
    name: str = Field(..., description="Name of the card")
    hash: str = Field(..., description="Hash of the card data")
    background: str = Field(..., description="Background information of the card")
