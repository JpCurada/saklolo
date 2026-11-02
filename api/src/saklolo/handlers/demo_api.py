"""Local demo API: the dispatcher dashboard and the phone simulator talk to this.

Run:  uv run python -m saklolo.handlers.demo_api [--call-cache] [--port 8000]
Docs: http://127.0.0.1:8000/docs
"""

import argparse
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, StringConstraints

from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.config import REPO_ROOT, get_settings
from saklolo.dataset.io import load_dataset
from saklolo.dispatch.models import CaseView, MessageRecord, ReceiveResult
from saklolo.dispatch.replay import ReplayBusyError, Replayer, ReplayStatus
from saklolo.dispatch.service import CaseStateError, DispatchService
from saklolo.domain.models import Channel, InboundMessage, OutboundMessage, Priority
from saklolo.handlers.wiring import build_pipeline_deps

DASHBOARD_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1600)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class MessageIn(BaseModel):
    sender: Name
    text: Text
    channel: Channel = Channel.WEB
    received_at: datetime | None = Field(default=None, description="Defaults to now")


class AssignIn(BaseModel):
    team: Name


class OverrideIn(BaseModel):
    priority: Priority
    reason: Text


class ReplayIn(BaseModel):
    split: str = Field(default="dev", pattern="^(dev|calibration)$")
    speed: float = Field(default=3600.0, gt=0, description="Storm seconds per real second")
    max_delay_s: float = Field(default=2.0, ge=0, le=30)


def create_app(service: DispatchService, replayer: Replayer, outbox: InMemoryOutbox) -> FastAPI:
    app = FastAPI(title="Saklolo demo API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=DASHBOARD_ORIGINS, allow_methods=["*"], allow_headers=["*"]
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(_message_routes(service, outbox))
    app.include_router(_case_routes(service))
    app.include_router(_replay_routes(replayer))
    return app


def _message_routes(service: DispatchService, outbox: InMemoryOutbox) -> APIRouter:
    router = APIRouter(tags=["messages"])

    @router.post("/messages", status_code=201)
    def receive(body: MessageIn) -> ReceiveResult:
        received_at = body.received_at or datetime.now(UTC)
        message = InboundMessage(
            sender=body.sender, text=body.text, channel=body.channel, received_at=received_at
        )
        return service.receive(message)

    @router.get("/messages")
    def messages() -> list[MessageRecord]:
        return service.messages()

    @router.get("/outbox")
    def sent(recipient: str | None = None) -> list[OutboundMessage]:
        return outbox.sent(recipient)

    return router


def _case_routes(service: DispatchService) -> APIRouter:
    router = APIRouter(prefix="/cases", tags=["cases"])

    @router.get("")
    def cases(include_closed: bool = False) -> list[CaseView]:
        return service.cases(include_closed=include_closed)

    @router.get("/{case_id}")
    def case(case_id: str) -> CaseView:
        return _or_404(lambda: service.case(case_id))

    @router.post("/{case_id}/assign")
    def assign(case_id: str, body: AssignIn) -> CaseView:
        return _or_404(lambda: service.assign(case_id, body.team))

    @router.post("/{case_id}/override")
    def override(case_id: str, body: OverrideIn) -> CaseView:
        return _or_404(lambda: service.override(case_id, body.priority, body.reason))

    @router.post("/{case_id}/confirm-safe")
    def confirm_safe(case_id: str) -> CaseView:
        return _or_404(lambda: service.confirm_safe(case_id))

    return router


def _replay_routes(replayer: Replayer) -> APIRouter:
    router = APIRouter(prefix="/replay", tags=["replay"])

    @router.post("", status_code=202)
    def start_replay(body: ReplayIn) -> ReplayStatus:
        try:
            return replayer.start(body.split, body.speed, body.max_delay_s)
        except ReplayBusyError as error:
            raise HTTPException(409, str(error)) from error

    @router.get("")
    def replay_status() -> ReplayStatus:
        return replayer.status()

    @router.delete("")
    def stop_replay() -> ReplayStatus:
        return replayer.stop()

    return router


def _or_404(action: Callable[[], CaseView]) -> CaseView:
    try:
        return action()
    except KeyError as error:
        raise HTTPException(404, f"unknown case {error}") from error
    except CaseStateError as error:
        raise HTTPException(409, str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--call-cache", action="store_true", help="Reuse cached model and embedding calls"
    )
    args = parser.parse_args()

    settings = get_settings()
    cache_dir = REPO_ROOT / "eval" / "cache" if args.call_cache else None
    dataset, problems = load_dataset(REPO_ROOT / "data")
    if problems:
        raise SystemExit("Dataset is invalid; run `python -m saklolo.dataset.validate`.")
    outbox = InMemoryOutbox()
    service = DispatchService(build_pipeline_deps(settings, call_cache_dir=cache_dir), outbox)
    app = create_app(service, Replayer(service, dataset), outbox)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
