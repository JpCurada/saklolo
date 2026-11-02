"""Builds the pipeline's dependencies. Shared by every composition root."""

import json
from datetime import timedelta
from pathlib import Path

import boto3

from saklolo.adapters.amazon_location import AmazonLocationGeocoder
from saklolo.adapters.archive import JsonlPostArchive
from saklolo.adapters.call_cache import CachingEmbedder, CachingStructuredModel, JsonlCache
from saklolo.adapters.corrections import AgentCoreCorrectionMemory, InMemoryCorrectionMemory
from saklolo.adapters.dynamodb import DynamoCaseStore, DynamoDispatchStore
from saklolo.adapters.geocode_cache import CachedGeocoder
from saklolo.adapters.hazard import GeoJsonFloodMap
from saklolo.adapters.memory import InMemoryCaseStore
from saklolo.adapters.offline import NoGeocoder, UnrecordedEmbedder, UnrecordedModel
from saklolo.adapters.strands_model import StrandsStructuredModel, bedrock_model
from saklolo.adapters.titan import EMBEDDING_DIMENSIONS, TitanEmbedder
from saklolo.agents.deps import PipelineDeps
from saklolo.agents.escalation import StrandsSwarmEscalation
from saklolo.agents.prompts import PromptSet
from saklolo.config import REPO_ROOT, Settings
from saklolo.domain.cases import DedupePolicy
from saklolo.domain.models import Location
from saklolo.domain.ports import CaseStore, CorrectionMemory, Embedder, StructuredModel

MODEL_CALLS_FILE = "model_calls.jsonl"
EMBEDDINGS_FILE = "embeddings.jsonl"
MANIFEST_FILE = "manifest.json"


FLOOD_MAP = REPO_ROOT / "data" / "hazard" / "marikina-flood-100yr.geojson"


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
    geocoder = CachedGeocoder(
        AmazonLocationGeocoder(session.client("geo-places", region_name=settings.location_region)),
        geocode_store,
    )
    corrections: CorrectionMemory = InMemoryCorrectionMemory()
    if settings.memory_id:
        corrections = AgentCoreCorrectionMemory(
            session.client("bedrock-agentcore"),
            settings.memory_id,
            settings.memory_strategy_id or None,
        )
    # The Swarm uses the strong model when one is set, else the fast one.
    escalation_model_id = settings.strong_model_id or settings.fast_model_id
    escalation = StrandsSwarmEscalation(bedrock_model(settings, escalation_model_id), geocoder)
    return PipelineDeps(
        model=model,
        geocoder=geocoder,
        embedder=embedder,
        cases=cases or InMemoryCaseStore(),
        dedupe=dedupe_policy(settings),
        escalation_threshold=settings.escalation_threshold,
        prompts=prompts or PromptSet.default(),
        model_id=settings.fast_model_id,
        escalation=escalation,
        corrections=corrections,
        escalation_model_id=escalation_model_id,
        archive=JsonlPostArchive(REPO_ROOT / "data" / "archive.jsonl"),
        flood_map=GeoJsonFloodMap(FLOOD_MAP),
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


def recorded_deps(
    settings: Settings,
    model_calls: JsonlCache,
    embeddings: JsonlCache,
    model_id: str,
    embedding_key: str,
) -> PipelineDeps:
    """No AWS clients at all: recorded calls, or a miss that keeps the message for a human."""
    return PipelineDeps(
        model=CachingStructuredModel(UnrecordedModel(), model_calls, model_id),
        geocoder=NoGeocoder(),
        embedder=CachingEmbedder(UnrecordedEmbedder(), embeddings, embedding_key),
        cases=InMemoryCaseStore(),
        dedupe=dedupe_policy(settings),
        escalation_threshold=settings.escalation_threshold,
        prompts=PromptSet.default(),
        model_id=f"{model_id} (recorded)",
        archive=JsonlPostArchive(REPO_ROOT / "data" / "archive.jsonl"),
        flood_map=GeoJsonFloodMap(FLOOD_MAP),
    )


def build_offline_deps(settings: Settings, cache_dir: Path) -> PipelineDeps:
    """The offline demo: calls recorded by handlers/record_demo_cache.py."""
    manifest = json.loads((cache_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    return recorded_deps(
        settings,
        JsonlCache(cache_dir / MODEL_CALLS_FILE),
        JsonlCache(cache_dir / EMBEDDINGS_FILE),
        manifest["model_id"],
        manifest["embedding_key"],
    )
