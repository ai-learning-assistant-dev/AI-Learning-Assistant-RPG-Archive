from pydantic import BaseModel, Field

from app.models.llm import LLMRequest
from app.utils.llm_client import LLM
from app.utils.logger import logger
from config.settings import settings


class ChatChain(BaseModel):
    llm: LLM = Field(default_factory=lambda: LLM(config=settings.base_llm))

    async def acall(self, user_message: str):
        request = LLMRequest(
            model=settings.base_llm.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        async for chunk in self.llm.astream(request):
            logger.info(chunk)
