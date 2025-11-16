from typing import Literal

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    get_buffer_string,
)
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.utils.logger import logger

from ..utils.model_config import modelSet
from .configuration import Configuration
from .prompts import (
    clarify_intension_prompt,
    final_output_prompt,
    play_core_prompt,
    supervisor_prompt,
    writer_prompt,
)
from .state import (
    AgentInputState,
    AgentState,
    ClarifyIntension,
    FinalResp,
    PlayCoreResp,
    SupervisorResp,
)


async def clarify_intension(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["supervisor", "__end__"]]:
    configurable = Configuration.from_runnable_config(config)
    messages = state["messages"]
    model_config = modelSet.models[configurable.common_model]
    if model_config is None:
        raise ValueError("model not found")
    model = ChatOpenAI(
        openai_api_key=model_config.model_provider.api_key,
        openai_api_base=model_config.model_provider.base_url,
        model_name=model_config.model,
    )

    if configurable.clarify_enable is False:
        return Command(
            goto="play_core",
            update={
                "query": messages[-1].content,
            },
        )

    clarification_model = model.with_structured_output(ClarifyIntension).with_retry(
        stop_after_attempt=2
    )

    logger.info(
        "llm call",
        extra={"stage": "clarify_intension", "history": get_buffer_string(messages)},
    )
    force = len(messages) / 2 + 1 >= configurable.max_clarify_turns
    prompt_content = clarify_intension_prompt.format(force=str(force).lower())

    resp = await clarification_model.ainvoke(
        [SystemMessage(content=prompt_content), *messages]
    )
    if resp.need_clarification:
        return Command(
            goto=END, update={"messages": [AIMessage(content=resp.question)]}
        )
    else:
        return Command(
            goto="play_core",
            update={
                "messages": [
                    AIMessage(content=resp.question)
                ],  # 此时questions是衔接术语
                "query": resp.verification,
            },
        )


async def play_core(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["play_complete"]]:
    configurable = Configuration.from_runnable_config(config)
    model_config = modelSet.models[configurable.common_model]
    if model_config is None:
        raise ValueError("model not found")
    model = ChatOpenAI(
        openai_api_key=model_config.model_provider.api_key,
        openai_api_base=model_config.model_provider.base_url,
        model_name=model_config.model,
    )
    play_core_model = model.with_structured_output(PlayCoreResp).with_retry(
        stop_after_attempt=2
    )
    prompt_content = play_core_prompt.format(query=state["query"])

    logger.info("llm call", extra={"stage": "play_core", "history": state["query"]})
    play_core_resp = await play_core_model.ainvoke(
        [HumanMessage(content=prompt_content)]
    )

    raw_note = f"""
    剧本名称：{play_core_resp.name}
    剧本背景：{play_core_resp.background}
    剧本事件链：{play_core_resp.eventChain}
    """
    return Command(
        goto="writer",
        update={
            "playname": play_core_resp.name,
            "background": play_core_resp.background,
            "eventChain": play_core_resp.eventChain,
            "writer_messages": {
                "type": "override",
                "value": [
                    SystemMessage(content=writer_prompt),
                    HumanMessage(content=raw_note),
                ],
            },
        },
    )


async def writer(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["play_complete", "supervisor"]]:
    configurable = Configuration.from_runnable_config(config)
    model_config = modelSet.models[configurable.common_model]
    if model_config is None:
        raise ValueError("model not found")
    model = ChatOpenAI(
        openai_api_key=model_config.model_provider.api_key,
        openai_api_base=model_config.model_provider.base_url,
        model_name=model_config.model,
    )
    loop_count = state.get("loop_count", 0)
    should_continue = state.get("should_continue", True)
    writer_messages = state.get("writer_messages", [])
    if not should_continue:
        return Command(
            goto="play_complete",
            update={
                "final": writer_messages[-1].content,
            },
        )

    writer_model = model.with_retry(stop_after_attempt=2)
    logger.info(
        "llm call",
        extra={"stage": "writer", "history": get_buffer_string(writer_messages)},
    )
    writer_resp = await writer_model.ainvoke(writer_messages)

    if loop_count < configurable.max_loop_count and should_continue:
        return Command(
            goto="supervisor",
            update={
                "loop_count": loop_count + 1,
                "writer_messages": [writer_resp],
            },
        )
    else:
        return Command(
            goto="play_complete",
            update={
                "writer_messages": [writer_resp],
                "final": writer_resp.content,
            },
        )


async def supervisor(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["supervisor"]]:
    configurable = Configuration.from_runnable_config(config)
    model_config = modelSet.models[configurable.common_model]
    if model_config is None:
        raise ValueError("model not found")
    model = ChatOpenAI(
        openai_api_key=model_config.model_provider.api_key,
        openai_api_base=model_config.model_provider.base_url,
        model_name=model_config.model,
    )
    writer_messages = state.get("writer_messages", [])
    most_recent_message = writer_messages[-1]
    supervisor_model = model.with_structured_output(SupervisorResp).with_retry(
        stop_after_attempt=2
    )
    prompt_content = supervisor_prompt.format(messages=most_recent_message)
    logger.info(
        "llm call",
        extra={"stage": "supervisor", "history": get_buffer_string(writer_messages)},
    )
    supervisor_resp = await supervisor_model.ainvoke(prompt_content)

    return Command(
        goto="writer",
        update={
            "writer_messages": [HumanMessage(content=supervisor_resp.advice)],
            "should_continue": supervisor_resp.should_continue,
        },
    )


async def play_complete(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    configurable = Configuration.from_runnable_config(config)
    model_config = modelSet.models[configurable.common_model]
    if model_config is None:
        raise ValueError("model not found")
    model = ChatOpenAI(
        openai_api_key=model_config.model_provider.api_key,
        openai_api_base=model_config.model_provider.base_url,
        model_name=model_config.model,
    )
    final = state.get("final", None)
    if final is None:
        raise ValueError("final not found")
    final_model = model.with_structured_output(FinalResp).with_retry(
        stop_after_attempt=2
    )
    prompt_content = final_output_prompt.format(text=final)
    logger.info("llm call", extra={"stage": "play_complete", "history": final})
    final_card = await final_model.ainvoke(prompt_content)
    return Command(
        goto=END,
        update={
            "final_card": final_card,
        },
    )


card_flow_builder = StateGraph(
    AgentState,
    input=AgentInputState,
    context_schema=[],
)

card_flow_builder.add_node("clarify_intension", clarify_intension)
card_flow_builder.add_node("play_core", play_core)
card_flow_builder.add_node("writer", writer)
card_flow_builder.add_node("supervisor", supervisor)
card_flow_builder.add_node("play_complete", play_complete)

card_flow_builder.add_edge(START, "clarify_intension")
card_flow_builder.add_edge("play_complete", END)

card_flow = card_flow_builder.compile()
