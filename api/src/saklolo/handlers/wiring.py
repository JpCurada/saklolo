"""Builds the pipeline's real AWS dependencies. Shared by every composition root."""

from datetime import timedelta
from pathlib import Path

import boto3

from saklolo.adapters.amazon_location import AmazonLocationGeocoder
from saklolo.adapters.call_cache import CachingEmbedder, CachingStructuredModel, JsonlCache
from saklolo.adapters.dynamodb import DynamoCaseStore, DynamoDispatchStore
from saklolo.adapters.geocode_cache import CachedGeocoder
from saklolo.adapters.memory import InMemoryCaseStore
from saklolo.adapters.strands_model import StrandsStructuredModel, bedrock_model
from saklolo.adapters.titan import EMBEDDING_DIMENSIONS, TitanEmbedder
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.prompts import PromptSet
from saklolo.config import Settings
from saklolo.domain.cases import DedupePolicy
from saklolo.domain.models import Location
from saklolo.domain.ports import CaseStore, Embedder, StructuredModel


def dedupe_policy(settings: Settings) -> DedupePolicy:
    return DedupePolicy(
        similarity_threshold=settings.dedupe_similarity_threshold,
        window=timedelta(hours=settings.dedupe_window_hours),
        radius_km=settings.dedupe_radius_km,
    )


def build_pipeline_deps(
    settings: Settings,
    cases: CaseStore | None = None,
    prompts: PromptSet | None = None,
    call_cache_dir: Path | None = None,
) -> PipelineDeps:
    """Real AWS adapters. With call_cache_dir, model and embedding calls are cached on disk."""
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    model: StructuredModel = StrandsStructuredModel(bedrock_model(settings, settings.fast_model_id))
    embedder: Embedder = TitanEmbedder(
        session.client("bedrock-runtime", region_name=settings.embedding_region),
        settings.embedding_model_id,
    )
    if call_cache_dir is not None:
        model = CachingStructuredModel(
            model, JsonlCache(call_cache_dir / "model_calls.jsonl"), settings.fast_model_id
        )
        embedder = CachingEmbedder(
            embedder,
            JsonlCache(call_cache_dir / "embeddings.jsonl"),
            f"{settings.embedding_model_id}:{EMBEDDING_DIMENSIONS}",
        )
    geocode_store: dict[str, Location | None] = {}
    return PipelineDeps(
        model=model,
        geocoder=CachedGeocoder(
            AmazonLocationGeocoder(
                session.client("geo-places", region_name=settings.location_region)
            ),
            geocode_store,
        ),
        embedder=embedder,
        cases=cases or InMemoryCaseStore(),
        dedupe=dedupe_policy(settings),
        escalation_threshold=settings.escalation_threshold,
        prompts=prompts or PromptSet.default(),
        model_id=settings.fast_model_id,
    )


def dynamo_stores(settings: Settings) -> tuple[DynamoCaseStore, DynamoDispatchStore] | None:
    """DynamoDB stores when all three tables are configured; None keeps state in memory."""
    tables = (settings.cases_table, settings.messages_table, settings.dispatch_table)
    if not any(tables):
        return None
    if not all(tables):
        raise ValueError(
            "Set all of SAKLOLO_CASES_TABLE, SAKLOLO_MESSAGES_TABLE, and SAKLOLO_DISPATCH_TABLE, "
            "or none of them."
        )
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    dynamodb = session.resource("dynamodb")
    cases, messages, dispatch = (dynamodb.Table(name) for name in tables)
    return DynamoCaseStore(cases), DynamoDispatchStore(messages, dispatch)
