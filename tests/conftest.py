import pytest

from backend.config.settings import Settings, get_settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        log_paths="",
        http_health_urls="http://127.0.0.1:1/health",
        ping_hosts="127.0.0.1",
        database_check_url="sqlite:///:memory:",
    )


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
