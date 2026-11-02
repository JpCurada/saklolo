"""Local demo API: the dispatcher dashboard and the phone simulator talk to this.

Run:  uv run python -m saklolo.handlers.demo_api [--call-cache] [--port 8000]
Docs: http://127.0.0.1:8000/docs
"""

import argparse
import json
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

import httpx
import uvicorn
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, StringConstraints

from saklolo.adapters.channels import ChannelNotifier, Send
from saklolo.adapters.messenger import MessengerClient, parse_webhook, signature_ok
from saklolo.adapters.outbox import InMemoryOutbox
from saklolo.adapters.telegram import TelegramBot, TelegramPoller
from saklolo.config import REPO_ROOT, ChannelSettings, get_settings
from saklolo.dataset.io import load_dataset
from saklolo.dispatch.models import CaseView, MessageRecord, ReceiveResult
from saklolo.dispatch.replay import ReplayBusyError, Replayer, ReplayStatus
from saklolo.dispatch.service import CaseStateError, DispatchService
from saklolo.domain.models import Channel, InboundMessage, OutboundMessage, Priority
from saklolo.handlers.wiring import build_pipeline_deps, dynamo_stores

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1600)]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class MessageIn(BaseModel):
    sender: Name
    text: Text
    channel: Channel = Channel.WEB
    received_at: datetime | None = Field(default=None, description="Defaults to now")


class DispatcherIn(BaseModel):
    dispatcher: Name = Field(description="Who made the decision; recorded in the case history")


class AssignIn(DispatcherIn):
    team: Name


class OverrideIn(DispatcherIn):
    priority: Priority
    reason: Text


class ReplayIn(BaseModel):
    split: str = Field(default="dev", pattern="^(dev|calibration)$")
    speed: float = Field(default=3600.0, gt=0, description="Storm seconds per real second")
    max_delay_s: float = Field(default=2.0, ge=0, le=30)


def create_app(
    service: DispatchService,
    replayer: Replayer,
    outbox: InMemoryOutbox,
    channels: ChannelSettings | None = None,
    origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Saklolo demo API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or get_settings().dashboard_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(_message_routes(service, outbox))
    app.include_router(_case_routes(service))
    app.include_router(_replay_routes(replayer))
    if channels is not None and channels.messenger_ready:
        app.include_router(_messenger_routes(service, channels))
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
        return _or_404(lambda: service.assign(case_id, body.team, body.dispatcher))

    @router.post("/{case_id}/override")
    def override(case_id: str, body: OverrideIn) -> CaseView:
        return _or_404(
            lambda: service.override(case_id, body.priority, body.reason, body.dispatcher)
        )

    @router.post("/{case_id}/confirm-safe")
    def confirm_safe(case_id: str, body: DispatcherIn) -> CaseView:
        return _or_404(lambda: service.confirm_safe(case_id, body.dispatcher))

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


def _messenger_routes(service: DispatchService, channels: ChannelSettings) -> APIRouter:
    router = APIRouter(prefix="/webhooks/messenger", tags=["channels"])
    if not (channels.messenger_app_secret and channels.messenger_verify_token):
        raise ValueError("Messenger needs an app secret and a verify token")
    app_secret = channels.messenger_app_secret.get_secret_value()
    verify_token = channels.messenger_verify_token.get_secret_value()

    @router.get("", response_class=PlainTextResponse)
    def verify(
        mode: Annotated[str, Query(alias="hub.mode")],
        token: Annotated[str, Query(alias="hub.verify_token")],
        challenge: Annotated[str, Query(alias="hub.challenge")],
    ) -> str:
        """Meta calls this once when the webhook is set up."""
        if mode != "subscribe" or token != verify_token:
            raise HTTPException(403, "verification failed")
        return challenge

    @router.post("")
    async def receive(request: Request, background: BackgroundTasks) -> dict[str, str]:
        body = await request.body()
        if not signature_ok(app_secret, body, request.headers.get("x-hub-signature-256")):
            raise HTTPException(403, "bad signature")
        # Answer Meta at once; the pipeline takes seconds per message.
        for message in parse_webhook(json.loads(body)):
            background.add_task(service.receive, message)
        return {"status": "received"}

    return router


def build_notifier(
    outbox: InMemoryOutbox, channels: ChannelSettings, http: httpx.Client
) -> tuple[ChannelNotifier, TelegramBot | None]:
    senders: dict[Channel, Send] = {}
    bot = None
    if channels.telegram_bot_token:
        bot = TelegramBot(channels.telegram_bot_token.get_secret_value(), http)
        senders[Channel.TELEGRAM] = bot.send
    if channels.messenger_ready and channels.messenger_page_token:
        token = channels.messenger_page_token.get_secret_value()
        senders[Channel.MESSENGER] = MessengerClient(
            token, channels.messenger_graph_version, http
        ).send
    return ChannelNotifier(outbox, senders), bot


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
    channels = ChannelSettings()
    notifier, bot = build_notifier(outbox, channels, httpx.Client())
    stores = dynamo_stores(settings)
    cases, store = stores if stores else (None, None)
    print(f"Saklolo state: {'DynamoDB' if stores else 'in memory (lost on restart)'}")
    deps = build_pipeline_deps(settings, cases=cases, call_cache_dir=cache_dir)
    service = DispatchService(deps, notifier, store)
    app = create_app(
        service, Replayer(service, dataset), outbox, channels, settings.dashboard_origins
    )
    if bot is not None:
        stop = threading.Event()
        threading.Thread(
            target=TelegramPoller(bot, service.receive).run, args=(stop,), daemon=True
        ).start()
        print("Telegram: polling for messages")
    if channels.messenger_ready:
        print("Messenger: webhook at /webhooks/messenger")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
