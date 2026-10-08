from typing import Optional
from .._base import AsyncTransport, SyncTransport
from ..types.auth import WsTicket


class WsTicketsResource:
    """Operations for minting single-use WebSocket authentication tickets."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(self, target: str, stream_session_id: Optional[str] = None) -> WsTicket:
        """
        Mint a single-use 30-second ticket for authenticating WebSockets.
        :param target: 'asr_call' or 'tts_text'
        :param stream_session_id: Optional bound session ID
        """
        payload = {"target": target}
        if stream_session_id:
            payload["stream_session_id"] = stream_session_id
        data = self._transport.request("POST", "/v1/ws/tickets", json=payload)
        return WsTicket.model_validate(data)


class AsyncWsTicketsResource:
    """Asynchronous operations for minting single-use WebSocket authentication tickets."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(self, target: str, stream_session_id: Optional[str] = None) -> WsTicket:
        """
        Mint a single-use 30-second ticket for authenticating WebSockets.
        :param target: 'asr_call' or 'tts_text'
        :param stream_session_id: Optional bound session ID
        """
        payload = {"target": target}
        if stream_session_id:
            payload["stream_session_id"] = stream_session_id
        data = await self._transport.request("POST", "/v1/ws/tickets", json=payload)
        return WsTicket.model_validate(data)
