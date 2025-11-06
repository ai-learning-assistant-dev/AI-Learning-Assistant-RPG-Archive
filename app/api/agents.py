import traceback

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from app.craftcard.configuration import Configuration
from app.craftcard.craftcard_agent import CraftcardAgent
from app.models.schemas import CraftCardRequest, StreamEvent
from app.models.store import ConversationType
from app.services.store_service import store_service
from app.utils.logger import logger

router = APIRouter()


@router.post("/craftcard")
async def craftcard(request: CraftCardRequest):
    """
    根据query制作一张角色卡 , sse接口推送中间过程
    """
    try:
        return StreamingResponse(
            craftcard_stream(request), media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(
            {
                "msg": f"Craftcard error: {str(e)}",
                "traceback": traceback.format_exc(),
            }
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


async def craftcard_stream(request: CraftCardRequest):
    craftcard_agent = CraftcardAgent()
    configure = Configuration(common_model=request.model).model_dump()

    message: list[str] = []
    if not request.session_id:
        # 首次请求
        session_id = await store_service.create_session(request.query)
    else:
        session_id = request.session_id

    conversation_id = await store_service.create_conversation(
        session_id=session_id,
        content=request.query,
        type=ConversationType.AGENT,
        parent_cid=request.parent_cid,
    )
    baseEvent = StreamEvent(
        session_id=session_id,
        conversation_id=conversation_id,
        parent_id=request.parent_cid,
    )
    yield f"data: {baseEvent.model_dump_json()}\n\n"
    async for event in craftcard_agent.craftcard_stream(
        message, config_dict=configure, session_id=session_id
    ):

        yield f"data: {event.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"
