from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Central project configuration. Values can come from defaults or from .env.
    app_env: str = "local"
    log_level: str = "INFO"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    pm_agent_url: str = "http://127.0.0.1:8011"
    ba_agent_url: str = "http://127.0.0.1:8012"
    da_agent_url: str = "http://127.0.0.1:8013"

    data_dir: Path = Field(default=Path("./data"))
    upload_dir: Path = Field(default=Path("./data/uploads"))
    rag_dir: Path = Field(default=Path("./data/rag"))
    chart_dir: Path = Field(default=Path("./data/charts"))
    max_ba_da_iterations: int = 3

    # extra="ignore" makes the .env configuration forgiving.
    # If extra environment variables are present, startup will not fail.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_dirs(self) -> None:
        # Keep runtime folders out of the code path. They are created automatically.
        for path in (self.data_dir, self.upload_dir, self.rag_dir, self.chart_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    # Cache settings so every file reads the same configuration without repeatedly parsing .env.
    settings = Settings()
    settings.ensure_dirs()
    return settings
