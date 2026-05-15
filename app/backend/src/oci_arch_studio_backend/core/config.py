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
    oci_auth_mode: str = Field(default="config_file", alias="OCI_AUTH_MODE")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    vector_db_url: str | None = Field(default=None, alias="VECTOR_DB_URL")
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")
    retrieval_provider: str = Field(default="local_json", alias="RETRIEVAL_PROVIDER")
    advisory_synthesis_provider: str = Field(
        default="deterministic",
        alias="ADVISORY_SYNTHESIS_PROVIDER",
    )
    oci_genai_chat_model_id: str | None = Field(
        default=None,
        alias="OCI_GENAI_CHAT_MODEL_ID",
    )
    oci_genai_max_tokens: int = Field(default=1200, alias="OCI_GENAI_MAX_TOKENS")
    oci_genai_temperature: float = Field(default=0.1, alias="OCI_GENAI_TEMPERATURE")
    oci_genai_embedding_model_id: str | None = Field(
        default=None,
        alias="OCI_GENAI_EMBEDDING_MODEL_ID",
    )
    oci_genai_compartment_id: str | None = Field(
        default=None,
        alias="OCI_GENAI_COMPARTMENT_ID",
    )
    oci_genai_endpoint: str | None = Field(default=None, alias="OCI_GENAI_ENDPOINT")
    oci_object_storage_namespace: str | None = Field(
        default=None,
        alias="OCI_OBJECT_STORAGE_NAMESPACE",
    )
    oci_vector_bucket: str | None = Field(default=None, alias="OCI_VECTOR_BUCKET")
    oci_vector_object_name: str = Field(
        default="knowledge/oci-rag-index.json",
        alias="OCI_VECTOR_OBJECT_NAME",
    )
    oci_vector_index_name: str | None = Field(default=None, alias="OCI_VECTOR_INDEX_NAME")
    oci_vector_db_dsn: str | None = Field(default=None, alias="OCI_VECTOR_DB_DSN")
    oci_vector_db_user: str | None = Field(default=None, alias="OCI_VECTOR_DB_USER")
    oci_vector_db_password: str | None = Field(default=None, alias="OCI_VECTOR_DB_PASSWORD")
    oci_vector_table_name: str = Field(
        default="OCI_ARCHITECTURE_CHUNKS",
        alias="OCI_VECTOR_TABLE_NAME",
    )
    knowledge_index_path: Path = Field(
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json",
        alias="KNOWLEDGE_INDEX_PATH",
    )
    release_snapshot_path: Path = Field(
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-release-snapshot.json",
        alias="RELEASE_SNAPSHOT_PATH",
    )
    frontend_dist_path: Path = Field(
        default=REPO_ROOT / "app" / "frontend" / "dist",
        alias="FRONTEND_DIST_PATH",
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

    @field_validator("release_snapshot_path")
    @classmethod
    def resolve_release_snapshot_path(cls, value: Path) -> Path:
        if value.is_absolute():
            return value
        return REPO_ROOT / value

    @field_validator("frontend_dist_path")
    @classmethod
    def resolve_frontend_dist_path(cls, value: Path) -> Path:
        if value.is_absolute():
            return value
        return REPO_ROOT / value


@lru_cache
def get_settings() -> Settings:
    return Settings()
