import operator
from typing import Annotated

from langchain_core.messages import MessageLikeRepresentation
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
    loop_count: int = 0
    should_continue: bool = True
    writer_messages: Annotated[list[MessageLikeRepresentation], override_reducer]
    final: str
    final_card: "FinalResp"


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


class SupervisorResp(BaseModel):
    """Model for supervisor response."""

    should_continue: bool = Field(
        description="布尔值是否继续创作",
    )
    advice: str = Field(
        description="具体的改进建议，使剧本更符合要求",
    )


class Character(BaseModel):
    name: str = Field(
        description="角色名称",
    )
    description: str = Field(
        description="角色简介",
    )


class Event(BaseModel):
    name: str = Field(
        description="事件名称",
    )
    description: str = Field(
        description="事件的详细描述",
    )


class FinalResp(BaseModel):
    """Model for final response."""

    first_msg: str = Field(
        description="第一幕的文本",
    )
    alternate_msgs: list[str] = Field(
        description="备选的第一幕文本",
    )
    main_character: Character = Field(
        description="主角",
    )
    others: list[Character] = Field(
        description="其他角色",
    )
    events: list[Event] = Field(
        description="事件",
    )
