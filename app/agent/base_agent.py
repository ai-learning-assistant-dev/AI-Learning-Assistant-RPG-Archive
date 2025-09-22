from abc import ABC, abstractmethod
from typing import AsyncGenerator

from app.models.llm import LLMResponse
from app.utils.llm_client import LLMClient
from app.utils.model_config import AgentConfig


class BaseAgent(ABC):
    """
    Base class for LLM-based agents.
    """

    llm_client: LLMClient

    def __init__(self, agent_config: AgentConfig):
        self.llm_client = LLMClient(config=agent_config.model)
        self.max_steps = agent_config.max_steps

    @abstractmethod
    async def acall(self, user_message: str) -> LLMResponse:
        pass

    @abstractmethod
    async def astream(self, user_message: str) -> AsyncGenerator[str, None]:
        pass
