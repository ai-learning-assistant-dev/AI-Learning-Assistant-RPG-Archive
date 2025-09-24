from datetime import datetime
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage

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
        self, query: str
    ) -> AsyncGenerator[CraftStreamingEvent, None]:
        yield CraftStreamingEvent(
            type="stage_start",
            stage=self.current_stage,
            content="Craftcard start",
            timestamp=datetime.now().isoformat(),
        )
        initial_state = AgentInputState(messages=[HumanMessage(content=query)])
        logger.info(f"Craftcard initial state: {initial_state}")
