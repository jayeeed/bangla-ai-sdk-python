from types import TracebackType
from typing import Any, Dict, Optional, Type
from ._base import _BaseConfig, AsyncTransport, SyncTransport
from ._constants import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT
from .resources.api_keys import ApiKeysResource, AsyncApiKeysResource
from .resources.asr import ASRResource, AsyncASRResource
from .resources.chats import AsyncChatsResource, ChatsResource
from .resources.me import AsyncMeResource, MeResource
from .resources.ocr import AsyncOCRResource, OCRResource
from .resources.sts import AsyncSTSResource, STSResource
from .resources.tts import AsyncTTSResource, TTSResource
from .resources.ws_tickets import AsyncWsTicketsResource, WsTicketsResource


class BanglaAI:
    """
    Synchronous client for the Bangla AI Gateway.

    Usage:
        from bangla_ai import BanglaAI

        client = BanglaAI(api_key="sk_live_...")
        # or reads BANGLA_AI_API_KEY from environment:
        client = BanglaAI()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        config = _BaseConfig(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
        )
        self._transport = SyncTransport(config)

        # Modality Sub-resources
        self.me = MeResource(self._transport)
        self.api_keys = ApiKeysResource(self._transport)
        self.ws_tickets = WsTicketsResource(self._transport)
        self.chats = ChatsResource(self._transport)
        self.ocr = OCRResource(self._transport)
        self.asr = ASRResource(self._transport)
        self.tts = TTSResource(self._transport)
        self.sts = STSResource(self._transport)

    def health(self) -> Dict[str, Any]:
        """Check gateway liveness."""
        return self._transport.request("GET", "/healthz")

    def ready(self) -> Dict[str, Any]:
        """Check composite readiness of database, redis, minio, and upstreams."""
        return self._transport.request("GET", "/readyz")

    def close(self) -> None:
        """Close the underlying HTTP client session."""
        self._transport.close()

    def __enter__(self) -> "BanglaAI":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()


class AsyncBanglaAI:
    """
    Asynchronous client for the Bangla AI Gateway.

    Usage:
        from bangla_ai import AsyncBanglaAI

        async with AsyncBanglaAI(api_key="sk_live_...") as client:
            chats = await client.chats.list()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        config = _BaseConfig(
            api_key=api_key,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            headers=headers,
        )
        self._transport = AsyncTransport(config)

        # Modality Sub-resources
        self.me = AsyncMeResource(self._transport)
        self.api_keys = AsyncApiKeysResource(self._transport)
        self.ws_tickets = AsyncWsTicketsResource(self._transport)
        self.chats = AsyncChatsResource(self._transport)
        self.ocr = AsyncOCRResource(self._transport)
        self.asr = AsyncASRResource(self._transport)
        self.tts = AsyncTTSResource(self._transport)
        self.sts = AsyncSTSResource(self._transport)

    async def health(self) -> Dict[str, Any]:
        """Check gateway liveness."""
        return await self._transport.request("GET", "/healthz")

    async def ready(self) -> Dict[str, Any]:
        """Check composite readiness of database, redis, minio, and upstreams."""
        return await self._transport.request("GET", "/readyz")

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        await self._transport.aclose()

    async def __aenter__(self) -> "AsyncBanglaAI":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()
