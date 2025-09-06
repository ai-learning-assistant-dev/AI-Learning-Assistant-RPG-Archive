"""
Model management API endpoints for LLM configuration and status.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.agent.chatagent import ChatAgent
from app.models.schemas import ChatRequest, CraftCardRequest
from app.utils.model_config import AgentConfig, model_config

router = APIRouter()


@router.post("/chat")
async def Chat(request: ChatRequest):
    llm = model_config.models.get("local_model", None)
    if llm is None:
        raise HTTPException(status_code=404, detail="Model not found")
    config = AgentConfig(model=llm)
    cc = ChatAgent(config)
    if request.stream:
        return StreamingResponse(
            cc.astream(request.message), media_type="text/event-stream"
        )
    else:
        data = await cc.acall(request.message)
        return JSONResponse(content=data.model_dump())


@router.post("/craftcard")
async def Craftcard(request: CraftCardRequest):
    return JSONResponse(content={"message": "Craftcard"})
