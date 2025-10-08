import asyncio
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from ..utils.model_config import modelSet
from .configuration import Configuration
from .prompts import clarify_intension_prompt, play_core_prompt, text_expand_prompt
from .state import (
    AgentInputState,
    AgentState,
    ClarifyIntension,
    PlayCoreResp,
    TextExpandResp,
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
    clarification_model = model.with_structured_output(ClarifyIntension).with_retry(2)
    prompt_content = clarify_intension_prompt.format(
        messages=get_buffer_string(messages)
    )

    resp = await clarification_model.ainvoke([HumanMessage(content=prompt_content)])

    if resp.need_clarification:
        return Command(
            goto=END, update={"messages": [AIMessage(content=resp.question)]}
        )
    else:
        return Command(
            goto="play_core",
            update={
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
    play_core_model = model.with_structured_output(PlayCoreResp).with_retry(2)
    prompt_content = play_core_prompt.format(query=state["query"])
    play_core_resp = await play_core_model.ainvoke(
        [HumanMessage(content=prompt_content)]
    )
    tasks = []

    async def expand_event(text: str) -> str:
        text_expand_model = model.with_structured_output(TextExpandResp).with_retry(2)
        prompt_content = text_expand_prompt.format(
            text=text, background=play_core_resp.background
        )
        resp = await text_expand_model.ainvoke([HumanMessage(content=prompt_content)])
        return resp.text

    for event in play_core_resp.eventChain:
        tasks.append(asyncio.create_task(expand_event(event)))
    await asyncio.gather(*tasks)


async def play_complete(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    return Command(
        goto="__end__",
        update={
            "playname": state["playname"],
            "background": state["background"],
            "eventChain": state["eventChain"],
        },
    )


card_flow_builder = StateGraph(
    AgentState,
    input=AgentInputState,
    context_schema=[],
)
