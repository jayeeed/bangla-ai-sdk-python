from typing import Any, AsyncGenerator, Dict, Generator, Optional
from .._base import AsyncTransport, SyncTransport
from ..types.tts import CustomReferenceAudio, TTSDiscovery


class TTSResource:
    """Operations for Speech Synthesis (Higgs TTS 3)."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def synthesize(
        self,
        text: str,
        voice: str = "male",
        first_segment_max_chars: int = 45,
    ) -> bytes:
        """
        Full-response voice synthesis returning complete audio/wav bytes.
        """
        payload = {
            "text": text,
            "voice": voice,
            "first_segment_max_chars": first_segment_max_chars,
        }
        return self._transport.request("POST", "/v1/tts/simple", json=payload)

    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "male",
        first_segment_max_chars: int = 45,
    ) -> str:
        """
        Synthesize text and save directly to a .wav audio file.
        """
        wav_bytes = self.synthesize(text, voice=voice, first_segment_max_chars=first_segment_max_chars)
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        return output_path

    def stream_pcm(
        self,
        text: str,
        voice: str = "male",
        first_segment_max_chars: int = 45,
    ) -> Generator[bytes, None, None]:
        """
        Low-latency streamed 24 kHz mono signed 16-bit PCM bytes.
        """
        payload = {
            "text": text,
            "voice": voice,
            "first_segment_max_chars": first_segment_max_chars,
        }
        for chunk in self._transport.stream_bytes("/v1/tts/simple/stream", json_body=payload):
            yield chunk

    def advanced(
        self,
        input: str,
        voice: Optional[str] = "female",
        model: str = "bosonai/higgs-tts-3-4b",
        speed: float = 1.0,
        response_format: str = "wav",
        custom_reference: Optional[CustomReferenceAudio] = None,
    ) -> bytes:
        """
        Advanced voice synthesis with custom zero-shot voice cloning.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "input": input,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
            "stream": False,
        }
        if custom_reference:
            payload["custom_reference"] = custom_reference.model_dump()

        return self._transport.request("POST", "/v1/tts/advanced", json=payload)

    def models(self) -> TTSDiscovery:
        """Discover available TTS models and default speaker voice presets."""
        res = self._transport.request("GET", "/v1/tts/models")
        return TTSDiscovery.model_validate(res)


class AsyncTTSResource:
    """Asynchronous operations for Speech Synthesis (Higgs TTS 3)."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def synthesize(
        self,
        text: str,
        voice: str = "male",
        first_segment_max_chars: int = 45,
    ) -> bytes:
        """
        Full-response voice synthesis returning complete audio/wav bytes.
        """
        payload = {
            "text": text,
            "voice": voice,
            "first_segment_max_chars": first_segment_max_chars,
        }
        return await self._transport.request("POST", "/v1/tts/simple", json=payload)

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "male",
        first_segment_max_chars: int = 45,
    ) -> str:
        """
        Synthesize text and save directly to a .wav audio file.
        """
        wav_bytes = await self.synthesize(text, voice=voice, first_segment_max_chars=first_segment_max_chars)
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        return output_path

    async def stream_pcm(
        self,
        text: str,
        voice: str = "male",
        first_segment_max_chars: int = 45,
    ) -> AsyncGenerator[bytes, None]:
        """
        Low-latency streamed 24 kHz mono signed 16-bit PCM bytes.
        """
        payload = {
            "text": text,
            "voice": voice,
            "first_segment_max_chars": first_segment_max_chars,
        }
        async for chunk in self._transport.stream_bytes("/v1/tts/simple/stream", json_body=payload):
            yield chunk

    async def advanced(
        self,
        input: str,
        voice: Optional[str] = "female",
        model: str = "bosonai/higgs-tts-3-4b",
        speed: float = 1.0,
        response_format: str = "wav",
        custom_reference: Optional[CustomReferenceAudio] = None,
    ) -> bytes:
        """
        Advanced voice synthesis with custom zero-shot voice cloning.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "input": input,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
            "stream": False,
        }
        if custom_reference:
            payload["custom_reference"] = custom_reference.model_dump()

        return await self._transport.request("POST", "/v1/tts/advanced", json=payload)

    async def models(self) -> TTSDiscovery:
        """Discover available TTS models and default speaker voice presets."""
        res = await self._transport.request("GET", "/v1/tts/models")
        return TTSDiscovery.model_validate(res)
