from typing import Any

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """Main configuration class for the card craft agent"""

    common_model: str = Field(default="default")

    common_model_provider: str = Field(default="")

    max_loop_count: int = Field(default=3, description="最大ReAct次数")

    clarify_enable: bool = Field(default=True, description="是否开启意图澄清")

    max_clarify_turns: int = Field(default=3, description="最大意图澄清轮数")

    @classmethod
    def from_runnable_config(cls, config: RunnableConfig | None) -> "Configuration":
        configurable = config.get("configurable", {}) if config else {}
        field_names = list(cls.model_fields.keys())
        values: dict[str, Any] = {
            field_name: configurable.get(field_name) for field_name in field_names
        }
        return cls(**{k: v for k, v in values.items() if v is not None})
