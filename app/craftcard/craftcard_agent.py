import uuid
from datetime import datetime
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage

from app.craftcard.configuration import Configuration
from app.craftcard.graph import card_flow
from app.craftcard.state import AgentInputState
from app.models.card import CraftStreamingEvent, ResearchStage
from app.utils.logger import logger


class CraftcardAgent:
    def __init__(self):
        self.max_steps = 10
        self.token_limit = 10000
        self.current_stage = ResearchStage.INITIALIZATION

    """ 制作角色卡的agent """

    async def craftcard_stream(
        self, query: str, *, config: Configuration
    ) -> AsyncGenerator[CraftStreamingEvent, None]:

        yield CraftStreamingEvent(
            type="stage_start",
            stage=self.current_stage,
            content="开始制作剧本🚀",
            timestamp=datetime.now().isoformat(),
        )
        session_id = str(uuid.uuid4())
        logger.info("Craftcard initial", extra={"session_id": session_id})
        input_state = AgentInputState(messages=[HumanMessage(content=query)])
        try:
            async for chunk in card_flow.astream(
                input_state, config=config, stream_mode="updates"
            ):
                logger.info("Craftcard chunk", extra={"chunk": chunk})
        except Exception as e:
            logger.error(f"Craftcard error: {str(e)}", extra={"session_id": session_id})
            raise e
