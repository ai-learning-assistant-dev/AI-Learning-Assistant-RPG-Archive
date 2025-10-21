import traceback

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from app.craftcard.configuration import Configuration
from app.craftcard.craftcard_agent import CraftcardAgent
from app.models.schemas import CraftCardRequest
from app.utils.logger import logger

router = APIRouter()


@router.post("/craftcard")
async def craftcard(request: CraftCardRequest):
    """
    根据query制作一张角色卡 , sse接口推送中间过程
    """

    async def craftcard_stream(request: CraftCardRequest):
        craftcard_agent = CraftcardAgent()
        configure = Configuration(
            common_model="deepseek-v3", clarify_enable=False
        ).model_dump()
        async for event in craftcard_agent.craftcard_stream(
            request.query, config_dict=configure
        ):
            yield f"data: {event.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

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
