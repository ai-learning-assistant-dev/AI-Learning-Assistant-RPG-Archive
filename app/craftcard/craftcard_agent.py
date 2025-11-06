import time
from datetime import datetime
from typing import Any, AsyncGenerator

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig

from app.craftcard.graph import card_flow
from app.craftcard.state import AgentInputState
from app.models.card import CraftStreamingEvent, ResearchStage
from app.utils.logger import logger


class CraftcardAgent:
    """制作角色卡的agent"""

    async def craftcard_stream(
        self, query: list[dict], *, config_dict: dict, session_id: str
    ) -> AsyncGenerator[CraftStreamingEvent, None]:
        """
        主流程异步迭代器
        """

        current_stage = ResearchStage.INITIALIZATION

        yield CraftStreamingEvent(
            stage=current_stage,
            content="🚀 开始制作剧本",
            timestamp=datetime.now().isoformat(),
        )

        messages = [
            BaseMessage(content=msg["content"], type=msg["type"]) for msg in query
        ]
        logger.info(
            "Craftcard initial", extra={"session_id": session_id, "msglist": messages}
        )

        input_state = AgentInputState(messages=messages)
        config = RunnableConfig(configurable=config_dict)
        node_count = 0
        chunk_start_time = time.time()
        try:
            async for chunk in card_flow.astream(
                input_state, config=config, stream_mode="updates"
            ):
                node_count += 1
                current_time = time.time()
                chunk_duration = current_time - chunk_start_time
                logger.info(
                    f"Processing chunk {node_count}: {list(chunk.keys())} (took {chunk_duration:.2f}s)",
                    extra={"session_id": session_id},
                )

                for node_name, node_data in chunk.items():
                    logger.info(f"Processing node: {node_name} (chunk {node_count})")
                    event = await self._process_node(
                        node_name, node_data, session_id, node_count
                    )
                    yield event

                chunk_start_time = current_time

        except Exception as e:
            logger.error(f"Craftcard error: {str(e)}", extra={"session_id": session_id})
            raise e

    async def _process_node(
        self, node_name: str, node_data: Any, session_id: str, node_count: int
    ) -> CraftStreamingEvent:
        """
        将langgraph返回的update的node处理为事件
        """

        async def _generate_node_content(
            stage: str,
            node_data: Any,
        ) -> str:

            logger.info(
                f"Generating Node: {node_name}, Raw_Data: {str(node_data)[:500]}",
                extra={"session_id": session_id},
            )
            content = ""
            match stage:
                case ResearchStage.CLARIFICATION:
                    content = "🔍 正在分析用户输入"
                    # TODO: 可以进一步细化澄清问题的内容
                case ResearchStage.PLAY_CORE:
                    content = "1️⃣ 核心内容生成中..."

                    if isinstance(node_data, dict):
                        name = node_data.get("playname", "未知剧本名称")
                        background = node_data.get("background", "未知背景信息")
                        event_chain = node_data.get("eventChain", [])
                        content += f"\n剧本名称: {name}\n背景: {background}\n"
                        for idx, event in enumerate(event_chain, start=1):
                            event_desc = event.get("name", "未知事件")
                            content += f"   {idx}. {event_desc}"
                case ResearchStage.WRITER:
                    content = "✍️ 剧本撰写中..."
                    if isinstance(node_data, dict) and "final" in node_data:
                        final_script = node_data["final"]
                        content += f"\n剧本内容预览:\n{final_script[:500]}..."
                    else:
                        content += "\n剧本内容正在生成中..."
                case ResearchStage.SUPERVISOR:
                    content = "🛡️ 反思检查中..."
                    # if isinstance(node_data, dict) and "writer_messages" in node_data:
                    #     advice = (
                    #         node_data["writer_messages"][-1].content
                    #         if "writer_messages" in node_data
                    #         else "无改进建议"
                    #     )
                    #     content += f"\n改进建议:\n{advice}"
                case ResearchStage.PLAY_COMPLETE:
                    content = "✅ 角色卡制作完成!"
                case ResearchStage.EXECUTION:
                    content = str(node_data)[:100]

            return content

        stage_mapping = {
            "clarify_intension": ResearchStage.CLARIFICATION,
            "play_core": ResearchStage.PLAY_CORE,
            "writer": ResearchStage.WRITER,
            "supervisor": ResearchStage.SUPERVISOR,
            "play_complete": ResearchStage.PLAY_COMPLETE,
        }

        stage = stage_mapping.get(node_name, ResearchStage.EXECUTION)
        content = await _generate_node_content(stage, node_data)

        event = CraftStreamingEvent(
            stage=stage,
            content=content,
            timestamp=datetime.now().isoformat(),
        )

        return event
