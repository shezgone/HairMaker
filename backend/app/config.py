from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str

    # Replicate
    replicate_api_token: str

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # Redis (Upstash) - optional for local dev
    redis_url: str = "redis://localhost:6379"

    # App
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
