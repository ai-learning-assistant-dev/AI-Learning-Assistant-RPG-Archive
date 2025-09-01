"""
Model management API endpoints for LLM configuration and status.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.chain.chatchain import ChatChain
from app.models.schemas import ChatRequest
from app.utils.llm_client import LLM
from config.settings import settings

router = APIRouter()


@router.post("/chat")
async def Chat(request: ChatRequest):
    llm = LLM(config=settings.base_llm)
    cc = ChatChain(llm=llm)
    if request.stream:
        return StreamingResponse(cc.astream(request.message), media_type="text/event-stream")
    else:
        data = await cc.acall(request.message)
        return JSONResponse(content=data.model_dump())
