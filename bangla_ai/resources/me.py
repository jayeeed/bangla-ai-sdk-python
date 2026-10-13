from typing import Any, Dict, Optional
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

    def update(
        self,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserProfile:
        """Update user profile information (display name, avatar URL, preferences)."""
        payload: Dict[str, Any] = {}
        if display_name is not None:
            payload["display_name"] = display_name
        if avatar_url is not None:
            payload["avatar_url"] = avatar_url
        if preferences is not None:
            payload["preferences"] = preferences

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

    async def update(
        self,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserProfile:
        """Update user profile information (display name, avatar URL, preferences)."""
        payload: Dict[str, Any] = {}
        if display_name is not None:
            payload["display_name"] = display_name
        if avatar_url is not None:
            payload["avatar_url"] = avatar_url
        if preferences is not None:
            payload["preferences"] = preferences

        data = await self._transport.request("PATCH", "/v1/me", json=payload)
        return UserProfile.model_validate(data)
