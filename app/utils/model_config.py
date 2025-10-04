import yaml
from pydantic import BaseModel


class ModelProvider(BaseModel):
    """
    Model provider configuration
    不同云厂商的模型配置
    """

    base_url: str = "http://localhost:1234/v1"
    api_key: str | None = None
    provider: str | None = None


class ModelConfig(BaseModel):
    """
    Model configuration
    模型调用的各种参数
    """

    model: str = ""
    model_provider: ModelProvider = ModelProvider()
    max_tokens: int = 4096


class MCPServerConfig(BaseModel):
    """
    MCP server configuration
    TODO: 暂时没用上
    """


class AgentConfig(BaseModel):
    """
    Agent configuration
    """

    model: ModelConfig
    max_steps: int | None = None
    tools: list[str] | None = None

    # allow_mcp_servers: list[str]
    # mcp_servers_config: dict[str, MCPServerConfig]


class ConfigError(Exception):
    pass


class Config(BaseModel):
    model_providers: dict[str, ModelProvider] = {}
    models: dict[str, ModelConfig] = {}

    @classmethod
    def create(cls, *, config_file: str | None = None) -> "Config":
        if not config_file:
            raise ConfigError("config_file is required")

        try:
            with open(config_file, "r") as f:
                yaml_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError("Error parsing YAML file") from e

        config = cls()
        model_providers = yaml_config.get("model_providers", None)
        if model_providers is not None and len(model_providers.keys()) > 0:
            config_model_providers: dict[str, ModelProvider] = {}
            for model_provider_name, model_provider_config in model_providers.items():
                config_model_providers[model_provider_name] = ModelProvider(
                    **model_provider_config
                )
            config.model_providers = config_model_providers
        else:
            raise ConfigError("No model providers provided")

        models = yaml_config.get("models", None)
        if models is not None and len(models.keys()) > 0:
            config_models: dict[str, ModelConfig] = {}
            for model_name, model_config in models.items():
                if model_config["model_provider"] not in config_model_providers:
                    raise ConfigError(
                        f"Model provider {model_config['model_provider']} not found"
                    )
                model_config["model_provider"] = config_model_providers[
                    model_config["model_provider"]
                ]
                config_models[model_name] = ModelConfig(**model_config)
            config.models = config_models
        else:
            raise ConfigError("No models provided")

        return config


modelSet = Config.create(config_file="llm_config.yaml")
