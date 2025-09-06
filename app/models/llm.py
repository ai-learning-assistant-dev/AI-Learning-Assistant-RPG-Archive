from typing import List

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str = Field(None, description="消息角色，如 'user', 'assistant', 'system'")
    content: str = Field(...)


class LLMChoice(BaseModel):
    index: int = Field(..., description="选择项索引")
    message: LLMMessage | None = Field(None, description="非流式消息内容")
    delta: LLMMessage | None = Field(None, description="流式消息内容")
    finish_reason: str | None = Field(None, description="完成原因")


class LLMUsage(BaseModel):
    prompt_tokens: int = Field(..., description="提示词token数量")
    completion_tokens: int = Field(..., description="完成token数量")
    total_tokens: int = Field(..., description="总token数量")


class LLMRequest(BaseModel):
    model: str | None = Field(None, description="模型名称")
    messages: List[LLMMessage] = Field(...)
    stream: bool = Field(False, description="是否流式传输")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int | None = Field(None, gt=0, description="最大token数量")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="top_p参数")
    top_k: int | None = Field(None, ge=0, description="top_k参数")

    # TODO: 添加工具
    # tools: List[LLMTool] = Field(default_factory=list)


class LLMResponse(BaseModel):
    choices: List[LLMChoice] = Field(default_factory=list)
    created: int = Field(...)
    id: str = Field(...)
    model: str = Field(...)
    object: str = Field(default="chat.completion")
    usage: LLMUsage | None = Field(None)
