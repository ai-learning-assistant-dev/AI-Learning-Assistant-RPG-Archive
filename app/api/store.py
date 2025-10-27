from fastapi import APIRouter

from app.services.store_service import store_service

router = APIRouter()


@router.post("/session/create")
async def create_session():
    """Create a new session."""
    session_id = await store_service.create_session("New Session")
    return {"session_id": session_id}
