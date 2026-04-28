"""统一配置系统 - 基于 pydantic-settings"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === App ===
    app_name: str = Field(default="inkling", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    port: int = Field(default=8080, description="服务端口")

    # === Database ===
    database_url: str = Field(
        default="sqlite:///./inkling.db",
        description="数据库连接 URL",
    )

    # === LLM Provider ===
    provider_type: str = Field(default="mock", description="LLM 提供商类型")
    llm_api_key: str | None = Field(default=None, description="LLM API Key")
    llm_base_url: str | None = Field(default=None, description="LLM Base URL")
    llm_model: str | None = Field(default=None, description="LLM 模型名称")

    @property
    def is_mock(self) -> bool:
        return self.provider_type == "mock"

    @property
    def has_llm_config(self) -> bool:
        return bool(self.llm_api_key and self.llm_base_url and self.llm_model)


# 全局单例
_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置单例（支持延迟加载，方便测试时覆盖）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """重置配置单例（测试用）"""
    global _settings
    _settings = None
