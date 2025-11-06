"""
Pydantic models for sillytavern character card
酒馆角色卡格式
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ResearchStage(str, Enum):
    """研究阶段"""

    INITIALIZATION = "initialization"
    CLARIFICATION = "clarification"
    PLAY_CORE = "outline"
    WRITER = "writing"
    SUPERVISOR = "reActing"
    PLAY_COMPLETE = "complete"
    EXECUTION = "execution"


class CraftStreamingEvent(BaseModel):
    """制作角色卡的流式事件"""

    stage: Optional[ResearchStage] = Field(None, description="Current research stage")
    content: str = Field(..., description="Event content or message")
    FinalResp: dict = Field(default_factory=dict, description="Final response data")
    timestamp: str = Field(
        default_factory=datetime.now().isoformat,
        description="ISO timestamp of the event",
    )


# 酒馆数据
class RegexScript(BaseModel):  # 正则
    id: str
    scriptName: str
    findRegex: str
    replaceString: str
    trimStrings: List[str]
    placement: List[int]
    disabled: bool
    markdownOnly: bool
    promptOnly: bool
    runOnEdit: bool
    substituteRegex: int
    minDepth: Optional[int] = None
    maxDepth: Optional[int] = None


class CharacterBookEntryExtensions(BaseModel):  # 世界书单一条目的信息，有很多用不上
    position: int
    exclude_recursion: bool
    display_index: int
    probability: int
    useProbability: bool
    depth: int
    selectiveLogic: int
    group: str
    group_override: bool
    group_weight: int
    prevent_recursion: bool
    delay_until_recursion: bool
    scan_depth: Optional[int] = None
    match_whole_words: bool = False
    use_group_scoring: bool = False
    case_sensitive: bool = False
    automation_id: str = ""
    role: int = 0
    vectorized: bool = False
    sticky: int = 0
    cooldown: int = 0
    delay: int = 0
    match_persona_description: bool = False
    match_character_description: bool = False
    match_character_personality: bool = False
    match_character_depth_prompt: bool = False
    match_scenario: bool = False
    match_creator_notes: bool = False


class CharacterBookEntry(BaseModel):
    id: int
    keys: List[str]  # 关键词
    secondary_keys: List[str]  # 可选过滤器(st文本描述如此)
    comment: str  # 描述
    content: str  # 激活后替换的文本
    constant: bool  # 是否永久激活,为true就不管正则是否生效，都会插入世界书
    selective: bool  # 永久为true？不知道含义
    insertion_order: int  # 同一个插入位置的顺序，数字小的在上面
    enabled: bool  # 是否应用
    position: str  # 几个位置枚举 after_char
    use_regex: bool  # 大多为true
    extensions: CharacterBookEntryExtensions


class CharacterBook(BaseModel):
    entries: List[CharacterBookEntry]
    name: str


class Extensions(BaseModel):
    talkativeness: str
    fav: bool
    world: str
    depth_prompt: Dict[str, Any]
    regex_scripts: List[RegexScript]


class Data(BaseModel):
    name: str
    first_mes: str
    alternate_greetings: List[str]
    extensions: Extensions
    group_only_greetings: List[str]
    character_book: CharacterBook


class CharacterCardV3(BaseModel):
    name: str
    first_mes: str
    talkativeness: str
    spec: str
    spec_version: str
    data: Data
    create_date: str
