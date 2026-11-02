"""Application settings. The only module that reads environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SAKLOLO_", env_file=REPO_ROOT / ".env", extra="ignore"
    )

    # pydantic-settings doesn't export .env values, so AWS settings are read here
    # and passed to boto3 sessions explicitly by the composition roots.
    aws_region: str = Field(default="ap-southeast-1", validation_alias="AWS_REGION")
    aws_profile: str | None = Field(default=None, validation_alias="AWS_PROFILE")

    fast_model_id: str = ""
    strong_model_id: str = ""
    embedding_model_id: str = ""
    escalation_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    place_index: str = ""
    intake_queue_url: str = ""
    cases_table: str = ""
    messages_table: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
