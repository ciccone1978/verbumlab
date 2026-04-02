from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
import os

class Settings(BaseSettings):
    """
    Application settings and environment variable configuration.
    
    Uses pydantic-settings to load variables from the root .env file.
    """
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_USER: str = Field(default="admin")
    POSTGRES_PASSWORD: str = Field(default="admin123")
    POSTGRES_DB: str = Field(default="verbumlab")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_ECHO: bool = Field(default=False)

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # MinIO
    MINIO_ENDPOINT: str = Field(default="http://localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin123")
    MINIO_BUCKET_NAME: str = Field(default="verbumlab")

    # JWT
    SECRET_KEY: str = Field(default="your-super-secret-key-change-me", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    # Embeddings and LLM
    EMBEDDING_MODEL: str = Field(default="mxbai-embed-large", env="EMBEDDING_MODEL")
    LLM_MODEL: str = Field(default="qwen3:8b", env="LLM_MODEL")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    CHAT_HISTORY_LIMIT: int = Field(default=5, env="CHAT_HISTORY_LIMIT")

settings = Settings()
