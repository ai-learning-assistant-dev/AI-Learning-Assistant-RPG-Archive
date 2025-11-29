import asyncio
import os

from fastapi import APIRouter

from app.models.schemas import (
    ConversationListRequest,
    ConversationListResponse,
    DeleteSessionRequest,
    DeleteSessionResponse,
    SessionListRequest,
    SessionListResponse,
    standard_response,
)
from app.models.store import Conversation, Session
from app.services.store_service import store_service
from config.settings import settings

router = APIRouter()


@router.post("/session/list")
@standard_response()
async def sessions_list(param: SessionListRequest):
    """List sessions with pagination and search."""
    lists = await store_service.list_sessions(limit=param.limit, offset=param.offset)
    sessions = [Session.model_validate(session) for session in lists]
    return SessionListResponse(sessions=sessions)


@router.post("/conversation/list")
@standard_response()
async def list_conversations(param: ConversationListRequest):
    lists = await store_service.list_conversations(session_id=param.session_id)
    conversations = [
        Conversation.model_validate(conversation) for conversation in lists
    ]
    return ConversationListResponse(conversations=conversations)


@router.post("/session/delete")
@standard_response()
async def delete_session(param: DeleteSessionRequest):
    """Delete a session by its ID."""
    card = await store_service.get_cards_by_session(param.session_id)
    if card is not None:
        hash = card.get("hash", "")
        if hash:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None,
                    lambda: os.remove(
                        os.path.join(settings.card_folder, f"{hash}.json")
                    ),
                )
            except Exception:
                pass
    success = await store_service.delete_session(param.session_id)
    return DeleteSessionResponse(success=success)
