import time
from datetime import datetime
from typing import Any, AsyncGenerator

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from app.craftcard.graph import card_flow
from app.craftcard.state import AgentInputState
from app.models.card import (
    CharacterBook,
    CharacterBookEntry,
    CharacterCardV3,
    CraftStreamingEvent,
    Data,
    ResearchStage,
)
from app.models.store import Card
from app.services.store_service import store_service
from app.utils.logger import logger
from config.settings import settings


class CraftcardAgent(BaseModel):
    """制作角色卡的agent"""

    stage: ResearchStage = ResearchStage.INITIALIZATION
    session_id: str = ""
    messages: list[BaseMessage] = []

    async def craftcard_stream(
        self,
        config_dict: dict,
    ) -> AsyncGenerator[CraftStreamingEvent, None]:
        """
        主流程异步迭代器
        """
        session_id = self.session_id
        if self.stage == ResearchStage.INITIALIZATION:
            yield CraftStreamingEvent(
                stage=self.stage,
                content="🚀 开始制作剧本",
                timestamp=datetime.now().isoformat(),
            )

        logger.info(
            "Craftcard initial",
            extra={"session_id": session_id, "msglist": self.messages[-1].text()},
        )

        input_state = AgentInputState(messages=self.messages)
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
                    if isinstance(node_data, dict) and "query" in node_data:
                        # 已完成澄清阶段
                        content = "🔍 " + node_data["messages"][-1].content
                    else:
                        content = node_data["messages"][-1].content
                case ResearchStage.PLAY_CORE:
                    content = "1️⃣ 核心内容生成中..."

                    if isinstance(node_data, dict):
                        name = node_data.get("playname", "未知剧本名称")
                        background = node_data.get("background", "未知背景信息")
                        # event_chain = node_data.get("eventChain", [])
                        content += f"\n剧本名称: {name}\n背景: {background}\n"
                        # for idx, event in enumerate(event_chain, start=1):
                        #     event_desc = event.get("name", "未知事件")
                        #     content += f"   {idx}. {event_desc}"
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
        self.stage = stage
        content = await _generate_node_content(stage, node_data)

        event = CraftStreamingEvent(
            stage=stage,
            content=content,
            timestamp=datetime.now().isoformat(),
        )

        if stage == ResearchStage.PLAY_COMPLETE:
            final_card = node_data.get("final_card").model_dump() if node_data else None
            if final_card is None:
                raise ValueError("Final card data is missing")
            card = await self.store_card(final_card)
            event.FinalResp = card.model_dump()

        return event

    async def store_card(self, data: dict) -> Card:
        """导出角色卡"""
        import asyncio
        import hashlib
        import os

        logger.info("Storing final card", extra={"session_id": self.session_id})
        title = data.get("title")
        first_msg = data.get("first_msg")

        if not title or not first_msg:
            raise ValueError("Title or first message is missing in final card data")

        alternate_msgs = data.get("alternate_msgs", [])
        main_character = data.get("main_character", {})
        other = data.get("others", [])
        events = data.get("events", [])
        entries: list = []
        for char in [main_character] + other:
            entry = CharacterBookEntry(
                id=len(entries),
                keys=[char.get("name", "未知角色")],
                comment="角色背景",
                content=char.get("description", ""),
            )
            entries.append(entry)

        for event in events:
            entry = CharacterBookEntry(
                id=len(entries),
                keys=[event.get("name", "未知事件")],
                comment="事件描述",
                content=event.get("description", ""),
            )
            entries.append(entry)
        card = CharacterCardV3(
            name=title,
            first_mes=first_msg,
            data=Data(
                name=title,
                first_mes=first_msg,
                alternate_greetings=alternate_msgs,
                character_book=CharacterBook(entries=entries, name="世界书-" + title),
            ),
            create_date=datetime.now().isoformat(),
        )
        json_data = card.model_dump_json()
        hash_filename = hashlib.md5(json_data.encode("utf-8")).hexdigest()[:12]
        filename = f"{hash_filename}.json"

        def sync_write():
            with open(os.path.join(settings.card_folder, filename), "w") as f:
                f.write(json_data)

        # 使用线程池执行
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, sync_write)

        card_id = await store_service.create_card(
            session_id=self.session_id,
            name=card.name,
            hash=hash_filename,
            background=first_msg,
        )

        logger.info(
            f"Card stored with ID: {card_id}, Filename: {filename}",
            extra={"session_id": self.session_id},
        )

        return Card(
            id=card_id,
            session_id=self.session_id,
            name=card.name,
            hash=hash_filename,
            background=data.get("first_msg", ""),
        )
