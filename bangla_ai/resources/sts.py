import os
from typing import BinaryIO, Optional, Union
from .._base import AsyncTransport, SyncTransport
from ..types.sts import LiveKitToken, VoiceReference


class STSResource:
    """Operations for real-time Speech-to-Speech (STS) and voice clone conditioning."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def upload_voice_reference(
        self,
        file: Union[str, bytes, BinaryIO],
        filename: Optional[str] = None,
    ) -> VoiceReference:
        """
        Upload a .wav audio clip to clone a voice.
        Nemotron transcribes it, caches it for Higgs conditioning, and returns a reference_id.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "reference.wav"
            content = file
        else:
            fn = filename or getattr(file, "name", "reference.wav")
            content = file.read()

        files = {"file": (fn, content)}
        res = self._transport.post_multipart("/v1/sts/voice/reference", files=files)
        return VoiceReference.model_validate(res)

    def get_livekit_token(
        self,
        voice: Optional[str] = None,
        reference_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        mode: Optional[str] = None,
        tenant_id: str = "default",
        customer_id: str = "default",
        room_name: Optional[str] = None,
        participant_name: Optional[str] = None,
    ) -> LiveKitToken:
        """
        Mint a scoped LiveKit room token for real-time speech-to-speech calls.
        """
        payload = {
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "voice": voice,
            "reference_id": reference_id,
            "phone_number": phone_number,
            "mode": mode,
        }
        if room_name:
            payload["room_name"] = room_name
        if participant_name:
            payload["participant_name"] = participant_name

        res = self._transport.request("POST", "/v1/sts/livekit/token", json=payload)
        return LiveKitToken.model_validate(res)

    def create_token(
        self,
        voice: Optional[str] = None,
        reference_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        mode: Optional[str] = None,
        tenant_id: str = "default",
        customer_id: str = "default",
        room_name: Optional[str] = None,
        participant_name: Optional[str] = None,
    ) -> LiveKitToken:
        """Convenience alias for get_livekit_token."""
        return self.get_livekit_token(
            voice=voice,
            reference_id=reference_id,
            phone_number=phone_number,
            mode=mode,
            tenant_id=tenant_id,
            customer_id=customer_id,
            room_name=room_name,
            participant_name=participant_name,
        )


class AsyncSTSResource:
    """Asynchronous operations for real-time Speech-to-Speech (STS)."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def upload_voice_reference(
        self,
        file: Union[str, bytes, BinaryIO],
        filename: Optional[str] = None,
    ) -> VoiceReference:
        """
        Upload a .wav audio clip to clone a voice.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "reference.wav"
            content = file
        else:
            fn = filename or getattr(file, "name", "reference.wav")
            content = file.read()

        files = {"file": (fn, content)}
        res = await self._transport.post_multipart("/v1/sts/voice/reference", files=files)
        return VoiceReference.model_validate(res)

    async def get_livekit_token(
        self,
        voice: Optional[str] = None,
        reference_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        mode: Optional[str] = None,
        tenant_id: str = "default",
        customer_id: str = "default",
        room_name: Optional[str] = None,
        participant_name: Optional[str] = None,
    ) -> LiveKitToken:
        """
        Mint a scoped LiveKit room token for real-time speech-to-speech calls.
        """
        payload = {
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "voice": voice,
            "reference_id": reference_id,
            "phone_number": phone_number,
            "mode": mode,
        }
        if room_name:
            payload["room_name"] = room_name
        if participant_name:
            payload["participant_name"] = participant_name

        res = await self._transport.request("POST", "/v1/sts/livekit/token", json=payload)
        return LiveKitToken.model_validate(res)

    async def create_token(
        self,
        voice: Optional[str] = None,
        reference_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        mode: Optional[str] = None,
        tenant_id: str = "default",
        customer_id: str = "default",
        room_name: Optional[str] = None,
        participant_name: Optional[str] = None,
    ) -> LiveKitToken:
        """Convenience alias for get_livekit_token."""
        return await self.get_livekit_token(
            voice=voice,
            reference_id=reference_id,
            phone_number=phone_number,
            mode=mode,
            tenant_id=tenant_id,
            customer_id=customer_id,
            room_name=room_name,
            participant_name=participant_name,
        )
