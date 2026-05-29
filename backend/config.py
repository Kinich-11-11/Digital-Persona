from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")
    temperature: float = Field(default=0.75, alias="TEMPERATURE")
    top_p: float = Field(default=0.9, alias="TOP_P")
    max_tokens: int = Field(default=500, alias="MAX_TOKENS")
    target_person_name: str = Field(default="浅羽悠真", alias="TARGET_PERSON_NAME")
    user_person_name: str = Field(default="我", alias="USER_PERSON_NAME")
    chat_records_dir: Path = Field(default=Path("../聊天记录"), alias="CHAT_RECORDS_DIR")
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def resolve_paths(self) -> "Settings":
        base_dir = Path(__file__).resolve().parent
        self.chat_records_dir = (base_dir / self.chat_records_dir).resolve() if not self.chat_records_dir.is_absolute() else self.chat_records_dir
        self.data_dir = (base_dir / self.data_dir).resolve() if not self.data_dir.is_absolute() else self.data_dir
        return self

    @property
    def normalized_messages_path(self) -> Path:
        return self.data_dir / "normalized_messages.jsonl"

    @property
    def examples_path(self) -> Path:
        return self.data_dir / "examples.jsonl"

    @property
    def profile_path(self) -> Path:
        return self.data_dir / "persona_profile.json"

    @property
    def stats_path(self) -> Path:
        return self.data_dir / "stats.json"

    @property
    def vector_store_dir(self) -> Path:
        return self.data_dir / "vector_store"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
