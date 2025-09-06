from typing import AsyncGenerator

from pydantic import BaseModel, PrivateAttr

from app.models.llm import LLMRequest, LLMResponse
from app.utils.http_client import get_http_client
from app.utils.logger import logger
from app.utils.model_config import ModelConfig


class LLMClient(BaseModel):
    """
    LLM client
    目前只支持openai格式
    """

    config: ModelConfig
    _chat_completions_url: str = PrivateAttr()

    def __init__(self, config: ModelConfig):
        super().__init__(config=config)
        self._chat_completions_url = (
            self.config.model_provider.base_url + "/chat/completions"
        )

    async def astream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        header = {
            "Authorization": f"Bearer {self.config.model_provider.api_key}",
            "Content-Type": "application/json",
        }
        request = self._build_request(request)
        data = request.model_dump_json(exclude_none=True)
        url = self._chat_completions_url
        try:
            async with get_http_client().post(
                url, headers=header, data=data
            ) as response:
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        line = line[6:]
                        if line == "[DONE]":
                            break
                        yield line
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            raise e

    async def acall(self, request: LLMRequest) -> LLMResponse:
        header = {
            "Authorization": f"Bearer {self.config.model_provider.api_key}",
            "Content-Type": "application/json",
        }
        request = self._build_request(request)
        data = request.model_dump_json(exclude_none=True)
        url = self._chat_completions_url
        try:
            async with get_http_client().post(
                url, headers=header, data=data
            ) as response:
                if response.status != 200:
                    raise Exception(f"LLM request error: {response.text}")
                data = await response.json()
            return LLMResponse.model_validate(data)
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            raise e

    def _build_request(self, request: LLMRequest) -> LLMRequest:
        if request.model is None:
            request.model = self.config.model
        if request.temperature is None:
            request.temperature = self.config.temperature
        if request.max_tokens is None:
            request.max_tokens = self.config.max_tokens
        if request.top_p is None:
            request.top_p = self.config.top_p
        if request.top_k is None:
            request.top_k = self.config.top_k
        return request
