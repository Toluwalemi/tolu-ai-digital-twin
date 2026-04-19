from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent

_ENV_CANDIDATES = (_BACKEND_DIR / ".env", _REPO_ROOT / ".env")
_ENV_FILE = next((p for p in _ENV_CANDIDATES if p.is_file()), None)


class Settings(BaseSettings):
    """Settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = ""
    chat_model: str = "google/gemini-2.5-flash-lite"
    openrouter_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    max_output_tokens: int = 500

    # GCS conversation memory
    gcs_bucket_name: str = ""

    # CORS
    cors_origins: str = "*"

    # App metadata (sent to OpenRouter)
    app_title: str = "Toluwalemi Digital Twin"
    app_referer: str = "https://toluwalemi.com"


settings = Settings()
