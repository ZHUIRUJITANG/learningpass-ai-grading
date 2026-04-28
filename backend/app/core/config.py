from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "learningpass-ai-grading"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres123@localhost:5432/learningpass"
    )

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET: str = "assignments"

    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = "mock"

    class Config:
        env_file = ".env"


settings = Settings()
