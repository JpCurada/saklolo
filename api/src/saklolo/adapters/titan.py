"""Embedder implemented with Amazon Titan Text Embeddings V2 on Bedrock."""

import json
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from saklolo.domain.errors import ServiceUnavailableError

EMBEDDING_DIMENSIONS = 256  # small vectors are enough to compare short case summaries


class TitanEmbedder:
    def __init__(self, bedrock_runtime: Any, model_id: str) -> None:
        self._client = bedrock_runtime
        self._model_id = model_id

    def embed(self, text: str) -> list[float]:
        body = {"inputText": text, "dimensions": EMBEDDING_DIMENSIONS, "normalize": True}
        try:
            response = self._client.invoke_model(modelId=self._model_id, body=json.dumps(body))
        except (BotoCoreError, ClientError) as error:
            raise ServiceUnavailableError(f"Titan embeddings failed: {error}") from error
        payload = json.loads(response["body"].read())
        return [float(x) for x in payload["embedding"]]
