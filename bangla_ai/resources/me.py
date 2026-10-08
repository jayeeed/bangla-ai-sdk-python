from typing import Optional
from .._base import AsyncTransport, SyncTransport
from ..types.auth import UserProfile


class MeResource:
    """Operations for the currently authenticated identity."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def get(self) -> UserProfile:
        """Fetch current user profile and quota tier."""
        data = self._transport.request("GET", "/v1/me")
        return UserProfile.model_validate(data)

    def update(self, display_name: Optional[str] = None) -> UserProfile:
        """Update user profile information (e.g. display name)."""
        payload = {}
        if display_name is not None:
            payload["display_name"] = display_name
        data = self._transport.request("PATCH", "/v1/me", json=payload)
        return UserProfile.model_validate(data)


class AsyncMeResource:
    """Asynchronous operations for the currently authenticated identity."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def get(self) -> UserProfile:
        """Fetch current user profile and quota tier."""
        data = await self._transport.request("GET", "/v1/me")
        return UserProfile.model_validate(data)

    async def update(self, display_name: Optional[str] = None) -> UserProfile:
        """Update user profile information (e.g. display name)."""
        payload = {}
        if display_name is not None:
            payload["display_name"] = display_name
        data = await self._transport.request("PATCH", "/v1/me", json=payload)
        return UserProfile.model_validate(data)
