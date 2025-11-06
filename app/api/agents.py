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
        logger.info(
            "Craftcard request started",
            extra={"session_id": request.session_id, "model": request.model},
        )
        return StreamingResponse(
            craftcard_stream(request), media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(
            f"Craftcard error: {str(e)}",
            extra={
                "session_id": request.session_id,
                "traceback": traceback.format_exc(),
            },
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


async def craftcard_stream(request: CraftCardRequest):
    craftcard_agent = CraftcardAgent()
    configure = Configuration(common_model=request.model).model_dump()

    logger.info(
        "Craftcard stream started",
        extra={"session_id": request.session_id, "query": request.query},
    )

    message: list[dict] = [{"content": request.query, "type": ConversationType.HUMAN}]
    if not request.session_id:
        # 首次请求
        session_id = await store_service.create_session(request.query)
    else:
        session_id = request.session_id
        old_message = await store_service.list_conversations(session_id)
        message = old_message + message

    parent_id = await store_service.create_conversation(
        session_id=session_id,
        content=request.query,
        type=ConversationType.HUMAN,
        parent_cid=request.parent_cid,
    )

    current_id = await store_service.create_conversation(
        session_id=session_id,
        content="",
        type=ConversationType.AI,
        parent_cid=parent_id,
    )

    baseEvent = StreamEvent(
        session_id=session_id,
        conversation_id=current_id,
        parent_id=parent_id,
    )
    content = ""
    async for event in craftcard_agent.craftcard_stream(
        message, config_dict=configure, session_id=session_id
    ):
        content += event.content + "\n"
        baseEvent.data = event.model_dump()
        yield f"data: {baseEvent.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"

    await store_service.update_conversation(
        conversation_id=current_id,
        content=content,
    )

    logger.info(
        "Craftcard completed",
        extra={
            "session_id": session_id,
        },
    )
