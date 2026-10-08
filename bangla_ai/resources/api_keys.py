from typing import List, Optional
from urllib.parse import quote
from .._base import AsyncTransport, SyncTransport
from ..types.auth import ApiKey


class ApiKeysResource:
    """Operations for developer API key provisioning and lifecycle."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        rate_limit_tier: Optional[str] = None,
        allowed_ips: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> ApiKey:
        """Provision a new developer API key."""
        payload = {"name": name}
        if scopes is not None:
            payload["scopes"] = scopes
        if rate_limit_tier is not None:
            payload["rate_limit_tier"] = rate_limit_tier
        if allowed_ips is not None:
            payload["allowed_ips"] = allowed_ips
        if allowed_origins is not None:
            payload["allowed_origins"] = allowed_origins
        if expires_in_days is not None:
            payload["expires_in_days"] = expires_in_days

        data = self._transport.request("POST", "/v1/api-keys", json=payload)
        return ApiKey.model_validate(data)

    def list(self) -> List[ApiKey]:
        """List all developer API keys provisioned for the current user."""
        data = self._transport.request("GET", "/v1/api-keys")
        return [ApiKey.model_validate(item) for item in data]

    def delete(self, key_id: str) -> None:
        """Revoke a developer API key instantly."""
        self._transport.request("DELETE", f"/v1/api-keys/{quote(str(key_id), safe='')}")


class AsyncApiKeysResource:
    """Asynchronous operations for developer API key provisioning and lifecycle."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(
        self,
        name: str,
        scopes: Optional[List[str]] = None,
        rate_limit_tier: Optional[str] = None,
        allowed_ips: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> ApiKey:
        """Provision a new developer API key."""
        payload = {"name": name}
        if scopes is not None:
            payload["scopes"] = scopes
        if rate_limit_tier is not None:
            payload["rate_limit_tier"] = rate_limit_tier
        if allowed_ips is not None:
            payload["allowed_ips"] = allowed_ips
        if allowed_origins is not None:
            payload["allowed_origins"] = allowed_origins
        if expires_in_days is not None:
            payload["expires_in_days"] = expires_in_days

        data = await self._transport.request("POST", "/v1/api-keys", json=payload)
        return ApiKey.model_validate(data)

    async def list(self) -> List[ApiKey]:
        """List all developer API keys provisioned for the current user."""
        data = await self._transport.request("GET", "/v1/api-keys")
        return [ApiKey.model_validate(item) for item in data]

    async def delete(self, key_id: str) -> None:
        """Revoke a developer API key instantly."""
        await self._transport.request("DELETE", f"/v1/api-keys/{quote(str(key_id), safe='')}")
