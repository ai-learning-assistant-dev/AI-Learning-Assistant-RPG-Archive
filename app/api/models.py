"""
Model management API endpoints for LLM configuration and status.
"""

from fastapi import APIRouter

from app.chain.chatchain import ChatChain
from app.models.schemas import ChatRequest
from app.utils.llm_client import LLM
from config.settings import settings

router = APIRouter()


@router.post("/chat")
async def Chat(request: ChatRequest):
    llm = LLM(config=settings.base_llm)
    cc = ChatChain(llm=llm)
    return await cc.acall(request.message)
