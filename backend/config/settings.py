from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "server-health-agent"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./data/incidents.db"

    google_api_key: str | None = None
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    agent_model: str = "gemini-2.0-flash"

    http_health_urls: str = "http://localhost:8000/health"
    ping_hosts: str = "8.8.8.8"
    monitored_ports: str = "80,443,8000"
    monitored_services: str = ""
    log_paths: str = ""
    database_check_url: str = "sqlite:///./data/incidents.db"

    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    memory_warning_percent: float = 85.0
    memory_critical_percent: float = 95.0
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 90.0

    http_timeout_seconds: float = Field(default=10.0)
    ping_timeout_seconds: float = Field(default=5.0)

    # Security
    api_key: str | None = None
    rate_limit_per_minute: int = 60
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    def csv_list(self, value: str) -> list[str]:
        if not value or not value.strip():
            return []
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
