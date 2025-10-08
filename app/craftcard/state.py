import operator

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


def override_reducer(current_value, new_value):
    """Reducer function that allows overriding values in state."""
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)
    else:
        return operator.add(current_value, new_value)


class AgentInputState(MessagesState):
    """InputState is only 'messages'."""


class AgentState(MessagesState):
    """Main agent state containing messages and research data."""

    query: str
    playname: str
    background: str
    eventChain: dict[str, str]
    character: dict[str, str]


class ClarifyIntension(BaseModel):
    """Model for user clarification requests."""

    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the intention",
    )
    verification: str = Field(
        description="Verify message that we will start story after the user has provided the necessary information.",
    )


class PlayCoreResp(BaseModel):
    """Model for play core response."""

    name: str = Field(
        description="剧本的名称，要求简洁明了，具有吸引力",
    )
    background: str = Field(
        description="剧本的背景，交代故事发生的世界背景，故事背景，核心冲突，待解决的目标",
    )
    eventChain: list[dict[str, str]] = Field(
        description="剧本的事件链，事件需要埋下线索，确保事件的逻辑自洽，确保事件的合理性，事件不少于6个",
    )


class TextExpandResp(BaseModel):
    """Model for text expand response."""

    text: str = Field(
        description="事件文本的扩写",
    )
