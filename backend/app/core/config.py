from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RAG Portfolio API"
    app_version: str = "0.1.0"
    environment: str = "local"
    cors_origins: list[str] = ["http://localhost:5173"]

    openai_api_key: str | None = None
    embedding_model: str = "embedding-3"
    chat_model: str = "deepseek-chat"
    deepseek_api_key: str | None = None
    deep_seek_api_key: str | None = None

    vectorstore_type: str = "chroma"
    chroma_persist_dir: str = "data/processed/chroma"
    database_url: str = "sqlite:///./rag.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    zhipu_api_key: str | None = None
    embedding_dimensions: int = 1024


settings = Settings()
