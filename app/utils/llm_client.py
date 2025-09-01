from typing import AsyncGenerator

from pydantic import BaseModel

from app.models.llm import LLMRequest, LLMResponse
from app.utils.http_client import get_http_client
from app.utils.logger import logger
from config.settings import LLMConfig, settings


class LLM(BaseModel):
    config: LLMConfig = settings.base_llm

    async def astream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        header = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        data = request.model_dump_json()
        url = self.config.url + "/chat/completions"
        try:
            async with get_http_client().post(url, headers=header, data=data) as response:
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
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        data = request.model_dump_json()
        url = self.config.url + "/chat/completions"
        try:
            async with get_http_client().post(url, headers=header, data=data) as response:
                if response.status != 200:
                    raise Exception(f"LLM request error: {response.status}")
                data = await response.json()
            return LLMResponse.model_validate(data)
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            raise e
