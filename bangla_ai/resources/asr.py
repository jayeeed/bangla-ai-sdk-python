import os
from typing import Any, BinaryIO, Dict, Optional, Union
from urllib.parse import quote
from .._base import AsyncTransport, SyncTransport
from ..types.asr import ASRResult, StreamChunk, StreamSession, YouTubeASRResult


class ASRResource:
    """Operations for Speech Recognition (ASR), YouTube transcription, and streaming."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def transcribe(
        self,
        file: Union[str, bytes, BinaryIO],
        diarize: bool = False,
        filename: Optional[str] = None,
    ) -> ASRResult:
        """
        Synchronous audio file transcription with optional speaker diarization.
        Supports WAV, MP3, OGG, FLAC, M4A, WebM.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "audio.wav"
            content = file
        else:
            fn = filename or getattr(file, "name", "audio.wav")
            content = file.read()

        files = {"file": (fn, content)}
        data = {"diarize": str(diarize).lower()}
        res = self._transport.post_multipart("/v1/asr/transcribe/offline", files=files, data=data)
        return ASRResult.model_validate(res)

    def transcribe_youtube(
        self,
        url: str,
        include_audio: bool = True,
        diarize: bool = True,
    ) -> YouTubeASRResult:
        """Transcribe audio from a YouTube video URL."""
        payload = {
            "url": url,
            "include_audio": include_audio,
            "diarize": diarize,
        }
        res = self._transport.request("POST", "/v1/asr/transcribe/youtube", json=payload)
        return YouTubeASRResult.model_validate(res)

    def create_stream(self, sample_rate: int = 16000) -> StreamSession:
        """Initiate a stateful live PCM16 speech recognition stream."""
        res = self._transport.request("POST", "/v1/asr/streams", params={"sample_rate": sample_rate})
        return StreamSession.model_validate(res)

    def stream_chunk(
        self,
        session_id: str,
        pcm_bytes: bytes,
        sample_rate: int = 16000,
        generation: int = 0,
        chunk_sequence: int = 0,
    ) -> StreamChunk:
        """Submit raw 16kHz signed 16-bit little-endian mono PCM audio bytes chunk."""
        params = {
            "sample_rate": sample_rate,
            "generation": generation,
            "chunk_sequence": chunk_sequence,
        }
        headers = {"Content-Type": "application/octet-stream"}
        url = f"/v1/asr/streams/{quote(str(session_id), safe='')}/chunk/pcm16"
        res = self._transport._client.post(
            f"{self._transport.config.base_url}{url}",
            content=pcm_bytes,
            params=params,
            headers=headers,
        )
        from .._base import _handle_error_response
        _handle_error_response(res)
        return StreamChunk.model_validate(res.json())

    def finish_stream(self, session_id: str) -> Dict[str, Any]:
        """Finalize live ASR stream and record usage."""
        return self._transport.request("POST", f"/v1/asr/streams/{quote(str(session_id), safe='')}/finish")

    def abort_stream(self, session_id: str) -> None:
        """Abort and release streaming session."""
        self._transport.request("DELETE", f"/v1/asr/streams/{quote(str(session_id), safe='')}")


class AsyncASRResource:
    """Asynchronous operations for Speech Recognition (ASR)."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def transcribe(
        self,
        file: Union[str, bytes, BinaryIO],
        diarize: bool = False,
        filename: Optional[str] = None,
    ) -> ASRResult:
        """
        Synchronous audio file transcription with optional speaker diarization.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "audio.wav"
            content = file
        else:
            fn = filename or getattr(file, "name", "audio.wav")
            content = file.read()

        files = {"file": (fn, content)}
        data = {"diarize": str(diarize).lower()}
        res = await self._transport.post_multipart("/v1/asr/transcribe/offline", files=files, data=data)
        return ASRResult.model_validate(res)

    async def transcribe_youtube(
        self,
        url: str,
        include_audio: bool = True,
        diarize: bool = True,
    ) -> YouTubeASRResult:
        """Transcribe audio from a YouTube video URL."""
        payload = {
            "url": url,
            "include_audio": include_audio,
            "diarize": diarize,
        }
        res = await self._transport.request("POST", "/v1/asr/transcribe/youtube", json=payload)
        return YouTubeASRResult.model_validate(res)

    async def create_stream(self, sample_rate: int = 16000) -> StreamSession:
        """Initiate a stateful live PCM16 speech recognition stream."""
        res = await self._transport.request("POST", "/v1/asr/streams", params={"sample_rate": sample_rate})
        return StreamSession.model_validate(res)

    async def stream_chunk(
        self,
        session_id: str,
        pcm_bytes: bytes,
        sample_rate: int = 16000,
        generation: int = 0,
        chunk_sequence: int = 0,
    ) -> StreamChunk:
        """Submit raw 16kHz signed 16-bit little-endian mono PCM audio bytes chunk."""
        params = {
            "sample_rate": sample_rate,
            "generation": generation,
            "chunk_sequence": chunk_sequence,
        }
        headers = {"Content-Type": "application/octet-stream"}
        url = f"/v1/asr/streams/{quote(str(session_id), safe='')}/chunk/pcm16"
        res = await self._transport._client.post(
            f"{self._transport.config.base_url}{url}",
            content=pcm_bytes,
            params=params,
            headers=headers,
        )
        from .._base import _handle_error_response
        _handle_error_response(res)
        return StreamChunk.model_validate(res.json())

    async def finish_stream(self, session_id: str) -> Dict[str, Any]:
        """Finalize live ASR stream and record usage."""
        return await self._transport.request("POST", f"/v1/asr/streams/{quote(str(session_id), safe='')}/finish")

    async def abort_stream(self, session_id: str) -> None:
        """Abort and release streaming session."""
        await self._transport.request("DELETE", f"/v1/asr/streams/{quote(str(session_id), safe='')}")
