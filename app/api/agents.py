from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.craftcard.configuration import Configuration
from app.craftcard.craftcard_agent import CraftcardAgent
from app.models.card import ResearchStage
from app.models.schemas import CraftCardRequest, StreamEvent
from app.models.store import ConversationType, SessionType
from app.services.store_service import store_service
from app.utils.logger import logger

router = APIRouter()


@router.post("/craftcard")
async def craftcard(request: CraftCardRequest):
    """
    根据query制作一张角色卡 , sse接口推送中间过程
    """
    return StreamingResponse(craftcard_stream(request), media_type="text/event-stream")


async def craftcard_stream(request: CraftCardRequest):

    configure = Configuration(common_model=request.model).model_dump()

    logger.info(
        "Craftcard stream started",
        extra={
            "session_id": request.session_id,
            "query": request.query,
            "model": request.model,
        },
    )

    message: list[BaseMessage] = [HumanMessage(content=request.query)]
    if not request.session_id:
        # 首次请求
        stage = ResearchStage.INITIALIZATION
        session_id = await store_service.create_session(
            request.query, SessionType.CRAFTCARD
        )
    else:
        stage = ResearchStage.CLARIFICATION
        session_id = request.session_id
        old_message = await store_service.list_conversations(session_id)
        format_message = []
        for msg in old_message:
            match msg["type"]:
                case ConversationType.HUMAN:
                    msg = HumanMessage(content=msg["content"])
                case ConversationType.AI:
                    msg = AIMessage(content=msg["content"])
                case _:
                    raise ValueError(f"Unknown message type: {msg['type']}")
            format_message.append(msg)
        message = format_message + message

    craftcard_agent = CraftcardAgent(
        stage=stage,
        session_id=session_id,
        messages=message,
    )

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
        config_dict=configure,
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
