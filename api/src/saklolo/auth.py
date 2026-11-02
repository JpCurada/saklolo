"""Dispatcher sign-in: Amazon Cognito access tokens, verified in the API.

Every route a dispatcher uses needs a signed-in member of the `dispatchers` group, and
the name in a case's history comes from the token, never from the request body. Only
`/health` and the channel webhooks (which check their own signatures) stay public.

Sign-in is required whenever a Cognito pool is configured. Without one the API runs
open, for local demos and tests, and it refuses to start that way inside AWS Lambda.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Annotated, Any, Protocol

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from saklolo.config import REPO_ROOT

logger = logging.getLogger(__name__)

DISPATCHERS_GROUP = "dispatchers"
SIGN_IN_REQUIRED = "Sign in required"
DISPATCHER_REQUIRED = "Dispatcher access required"
CLOCK_LEEWAY_S = 60
JWKS_CACHE_S = 3600
JWKS_TIMEOUT_S = 5


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SAKLOLO_",
        env_file=REPO_ROOT / ".env",
        extra="ignore",
        env_ignore_empty=True,
        populate_by_name=True,
    )

    cognito_region: str = "ap-southeast-1"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    # Set by the Lambda runtime; an open API is refused there.
    lambda_function: str = Field(default="", validation_alias="AWS_LAMBDA_FUNCTION_NAME")


class AuthenticationError(Exception):
    """The token is missing, malformed, unverifiable, or breaks a claim rule."""


class NotADispatcherError(Exception):
    """A valid token for someone outside the dispatchers group."""


@dataclass(frozen=True)
class CognitoPool:
    region: str
    user_pool_id: str
    client_id: str

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"


@dataclass(frozen=True)
class Dispatcher:
    """Who is acting. `verified` is False only on an open local API."""

    username: str
    verified: bool


class TokenDecoder(Protocol):
    def decode(self, token: str) -> Mapping[str, Any]:
        """Verified claims, or raise AuthenticationError."""
        ...


class CognitoTokenDecoder:
    """RS256 signature against the pool's public keys (cached), plus issuer and expiry."""

    def __init__(self, pool: CognitoPool) -> None:
        self._issuer = pool.issuer
        self._keys = jwt.PyJWKClient(
            pool.jwks_url, cache_jwk_set=True, lifespan=JWKS_CACHE_S, timeout=JWKS_TIMEOUT_S
        )

    def decode(self, token: str) -> Mapping[str, Any]:
        try:
            key = self._keys.get_signing_key_from_jwt(token).key
            claims: Mapping[str, Any] = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self._issuer,
                leeway=CLOCK_LEEWAY_S,
                # Cognito access tokens have no `aud`; the app client is checked below.
                options={"require": ["exp", "iss"], "verify_aud": False},
            )
        except jwt.PyJWTError as error:
            raise AuthenticationError(type(error).__name__) from error
        return claims


def dispatcher_from_claims(claims: Mapping[str, Any], client_id: str) -> Dispatcher:
    if claims.get("token_use") != "access":
        raise AuthenticationError("not an access token")
    if claims.get("client_id") != client_id:
        raise AuthenticationError("wrong app client")
    username = claims.get("username") or claims.get("cognito:username")
    if not isinstance(username, str) or not username.strip():
        raise AuthenticationError("no username")
    groups = claims.get("cognito:groups", [])
    if not isinstance(groups, list) or DISPATCHERS_GROUP not in groups:
        raise NotADispatcherError(username)
    return Dispatcher(username=username.strip(), verified=True)


_bearer = HTTPBearer(auto_error=False, description="Cognito access token of a dispatcher.")
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
OPEN = Dispatcher(username="", verified=False)


def dispatcher_dependency(
    settings: AuthSettings, decoder: TokenDecoder | None = None
) -> Callable[..., Dispatcher]:
    """The FastAPI dependency that every dispatcher route depends on."""
    configured = bool(settings.cognito_user_pool_id and settings.cognito_client_id)
    if not configured:
        if settings.lambda_function:
            raise RuntimeError(
                "Sign-in is required on AWS: set SAKLOLO_COGNITO_USER_POOL_ID and "
                "SAKLOLO_COGNITO_CLIENT_ID"
            )
        logger.warning("Cognito not configured: dispatcher routes are open (local only)")
        return lambda: OPEN

    pool = CognitoPool(
        settings.cognito_region, settings.cognito_user_pool_id, settings.cognito_client_id
    )
    verifier = decoder or CognitoTokenDecoder(pool)

    def require_dispatcher(credentials: Credentials) -> Dispatcher:
        try:
            if credentials is None:
                raise AuthenticationError("no bearer token")
            return dispatcher_from_claims(verifier.decode(credentials.credentials), pool.client_id)
        except AuthenticationError as error:
            logger.info("rejected token: %s", error)  # the reason, never the token
            raise HTTPException(
                401, SIGN_IN_REQUIRED, headers={"WWW-Authenticate": "Bearer"}
            ) from error
        except NotADispatcherError as error:
            raise HTTPException(403, DISPATCHER_REQUIRED) from error

    return require_dispatcher


def acting_name(dispatcher: Dispatcher, typed: str) -> str:
    """The token's username when signed in; on an open local API, the typed name."""
    return dispatcher.username if dispatcher.verified else typed
