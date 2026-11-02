"""Application settings. The only module that reads environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SAKLOLO_", env_file=REPO_ROOT / ".env", extra="ignore", env_ignore_empty=True
    )

    # pydantic-settings doesn't export .env values, so AWS settings are read here
    # and passed to boto3 sessions explicitly by the composition roots.
    aws_region: str = Field(default="ap-southeast-1", validation_alias="AWS_REGION")
    aws_profile: str | None = Field(default=None, validation_alias="AWS_PROFILE")

    fast_model_id: str = ""
    # USD per million tokens, from the Bedrock pricing page; used for cost metrics.
    fast_model_input_price: float = Field(default=0.0, ge=0.0)
    fast_model_output_price: float = Field(default=0.0, ge=0.0)
    strong_model_id: str = ""
    escalation_threshold: float = Field(default=0.75, ge=0.0, le=1.0)

    # Titan embeddings and Amazon Location geocoding aren't offered in every
    # region, so each has its own region setting (ADR 0005).
    embedding_model_id: str = "amazon.titan-embed-text-v2:0"
    embedding_region: str = "us-east-1"
    location_region: str = "ap-southeast-2"

    # Dedupe (ADR 0003): tune on the dev split only. 0.85 won notebook 02's sweep:
    # no neighboring households merged, best F1 (Titan V2, 256 dims).
    dedupe_similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    dedupe_window_hours: float = Field(default=12.0, gt=0)
    dedupe_radius_km: float = Field(default=1.5, gt=0)

    intake_queue_url: str = ""
    cases_table: str = ""
    messages_table: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
