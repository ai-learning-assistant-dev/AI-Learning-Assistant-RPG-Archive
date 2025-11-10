from fastapi import APIRouter

from app.models.schemas import (
    BaseResponse,
    ConversationListRequest,
    ConversationListResponse,
    SessionListRequest,
    SessionListResponse,
    standard_response,
)
from app.models.store import Conversation, Session
from app.services.store_service import store_service

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
async def delete_session(session_id: str):
    """Delete a session by its ID."""
    success = await store_service.delete_session(session_id)
    if not success:
        return BaseResponse.error(data=None)

    return BaseResponse.success(data=None)
