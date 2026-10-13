from typing import Any, Dict, Optional
from .._base import AsyncTransport, SyncTransport
from ..types.auth import GoogleAuthSyncResponse


class AuthResource:
    """Operations for user authentication and third-party identity synchronization."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def sync_google(
        self,
        id_token: Optional[str] = None,
        provider: str = "google",
    ) -> GoogleAuthSyncResponse:
        """
        Synchronize Google / Firebase authenticated identity with backend PostgreSQL user profile.
        Pass either an id_token or invoke with a configured Bearer token.
        """
        payload: Dict[str, Any] = {}
        if id_token:
            payload["id_token"] = id_token
        if provider:
            payload["provider"] = provider

        headers = {}
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"

        res = self._transport.request("POST", "/v1/auth/google", json=payload, headers=headers or None)
        return GoogleAuthSyncResponse.model_validate(res)


class AsyncAuthResource:
    """Asynchronous operations for user authentication and third-party identity synchronization."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def sync_google(
        self,
        id_token: Optional[str] = None,
        provider: str = "google",
    ) -> GoogleAuthSyncResponse:
        """
        Synchronize Google / Firebase authenticated identity with backend PostgreSQL user profile.
        """
        payload: Dict[str, Any] = {}
        if id_token:
            payload["id_token"] = id_token
        if provider:
            payload["provider"] = provider

        headers = {}
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"

        res = await self._transport.request("POST", "/v1/auth/google", json=payload, headers=headers or None)
        return GoogleAuthSyncResponse.model_validate(res)
