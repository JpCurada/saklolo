"""The agent trace: what each Graph step did, recorded while the graph runs."""

from dataclasses import replace

from saklolo.agents.graph import run_pipeline
from saklolo.agents.trace import STEP_ORDER
from saklolo.domain.models import TraceStatus, TraceStep
from tests.agents.fakes import fake_deps
from tests.agents.test_graph import fake_model, message


def by_step(trace: list[TraceStep]) -> dict[str, TraceStep]:
    return {step.step: step for step in trace}


def test_every_step_is_recorded_in_graph_order_with_the_model_named() -> None:
    deps = replace(fake_deps(fake_model()), model_id="apac.amazon.nova-lite-v1:0")

    trace = run_pipeline(message("nasa bubong na kami may baby 09171234567"), deps).trace

    assert [s.step for s in trace] == STEP_ORDER
    assert all(s.status == TraceStatus.RAN for s in trace)
    steps = by_step(trace)
    assert steps["normalize"].detail == "Cleaned the text; masked 1 phone number(s)"
    assert steps["extract"].service == "Bedrock · apac.amazon.nova-lite-v1:0"
    assert steps["triage"].service == "Bedrock · apac.amazon.nova-lite-v1:0"
    assert steps["geolocate"].service is None  # named in the text: no geocoder call
    assert steps["dedupe"].detail.startswith("Opened case-")
    assert steps["triage"].detail.startswith("P1: Infant on the roof (0.90, confident)")


def test_a_merge_shows_how_similar_the_reports_were() -> None:
    deps = fake_deps(fake_model())
    run_pipeline(message("nasa bubong kami"), deps)

    relative = run_pipeline(message("pamilya ko nasa bubong", sender="+639000000002"), deps)

    detail = by_step(relative.trace)["dedupe"].detail
    assert detail.startswith("Merged into case-0001: 1.00 similar")


def test_spam_shows_the_model_steps_as_skipped() -> None:
    model = fake_model()

    trace = run_pipeline(message("LEGIT LOAN APPROVAL 5 MINS"), fake_deps(model)).trace

    steps = by_step(trace)
    assert steps["prefilter"].detail.startswith("Flagged, not deleted")
    skipped = [s.step for s in trace if s.status == TraceStatus.SKIPPED]
    assert skipped == ["extract", "geolocate", "dedupe", "triage"]
    assert steps["extract"].detail == "Skipped: spam stops before any model call"
    assert model.calls == []
