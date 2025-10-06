from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from ..utils.model_config import modelSet
from .configuration import Configuration
from .prompts import clarify_intension_prompt
from .state import AgentInputState, AgentState, ClarifyIntension, SupervisorState


async def clarify_intension(state: AgentState, config: RunnableConfig):
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
            goto="supervisor",
            update={
                "messages": [AIMessage(content=resp.question)],
                "story_brief": resp.verification,
            },
        )


async def supervisor(state: SupervisorState):
    return Command()


card_flow_builder = StateGraph(
    AgentState,
    input=AgentInputState,
    context_schema=[],
)
