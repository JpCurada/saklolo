"""StructuredModel implemented with a Strands Agent and structured output."""

import boto3
from pydantic import BaseModel
from strands import Agent
from strands.models import BedrockModel, CacheConfig, Model

from saklolo.config import Settings
from saklolo.domain.errors import ModelOutputError
from saklolo.domain.ports import ModelCall, ModelUsage

MAX_OUTPUT_TOKENS = 1024


class StrandsStructuredModel:
    def __init__(self, model: Model) -> None:
        self._model = model

    def generate[OutputT: BaseModel](
        self, system_prompt: str, prompt: str, output_type: type[OutputT]
    ) -> ModelCall[OutputT]:
        # A fresh agent per call: no conversation history leaks between messages.
        agent = Agent(model=self._model, system_prompt=system_prompt, callback_handler=None)
        result = agent(prompt, structured_output_model=output_type)
        output = result.structured_output
        if not isinstance(output, output_type):
            raise ModelOutputError(f"expected {output_type.__name__}, got {type(output).__name__}")
        usage = result.metrics.accumulated_usage
        return ModelCall(
            output=output,
            usage=ModelUsage(
                input_tokens=usage["inputTokens"], output_tokens=usage["outputTokens"]
            ),
        )


def bedrock_model(settings: Settings, model_id: str) -> BedrockModel:
    if not model_id:
        raise ValueError("No Bedrock model ID configured; set SAKLOLO_FAST_MODEL_ID in .env")
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    # Automatic prompt caching is only supported for Claude models on Bedrock.
    cache_config = CacheConfig(strategy="auto") if "anthropic." in model_id else None
    return BedrockModel(
        model_id=model_id,
        boto_session=session,
        max_tokens=MAX_OUTPUT_TOKENS,
        cache_config=cache_config,
    )
