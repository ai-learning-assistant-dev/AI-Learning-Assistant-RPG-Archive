from abc import ABC, abstractmethod
from typing import AsyncGenerator

from pydantic import BaseModel

from app.models.llm import LLMResponse
from app.utils.llm_client import LLMClient
from app.utils.model_config import AgentConfig


class BaseAgent(BaseModel, ABC):
    """
    Base class for LLM-based agents.
    """

    llm_client: LLMClient

    def __init__(self, agent_config: AgentConfig):
        _llm_client = LLMClient(config=agent_config.model)
        super().__init__(llm_client=_llm_client)

    @abstractmethod
    async def acall(self, user_message: str) -> LLMResponse:
        pass

    @abstractmethod
    def astream(self, user_message: str) -> AsyncGenerator[str, None]:
        pass
