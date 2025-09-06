from typing import AsyncGenerator, override

from app.agent.base_agent import BaseAgent
from app.models.llm import LLMRequest, LLMResponse
from app.utils.logger import logger
from app.utils.model_config import AgentConfig


class ChatAgent(BaseAgent):
    """
    Chat agent for LLM-based agents.
    简单的对话，支持流式和非流式，主要用于测试
    """

    def __init__(self, agent_config: AgentConfig):
        super().__init__(agent_config)

    @override
    async def acall(self, user_message: str) -> LLMResponse:
        request = LLMRequest(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            stream=False,
        )
        return await self.llm_client.acall(request)

    @override
    async def astream(self, user_message: str) -> AsyncGenerator[str, None]:
        request = LLMRequest(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        async for line in self.llm_client.astream(request):
            logger.debug(f"line: {line}")
            yield f"data: {line}\n\n"
        yield "data: [DONE]\n\n"
