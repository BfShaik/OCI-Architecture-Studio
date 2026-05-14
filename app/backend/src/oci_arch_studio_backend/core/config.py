from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    oci_region: str | None = Field(default=None, alias="OCI_REGION")
    oci_profile: str = Field(default="DEFAULT", alias="OCI_PROFILE")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    vector_db_url: str | None = Field(default=None, alias="VECTOR_DB_URL")
    knowledge_index_path: Path = Field(
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json",
        alias="KNOWLEDGE_INDEX_PATH",
    )
    backend_cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="BACKEND_CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @field_validator("knowledge_index_path")
    @classmethod
    def resolve_knowledge_index_path(cls, value: Path) -> Path:
        if value.is_absolute():
            return value
        return REPO_ROOT / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
