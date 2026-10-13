import asyncio
import os
import time
from typing import Any, BinaryIO, Dict, List, Optional, Union

from .._base import AsyncTransport, SyncTransport
from ..types.asr import ASRJobAccepted, ASRJobStatus, ASRResult, StreamChunk, StreamSession, YouTubeASRResult


def _prepare_audio_file(
    file: Union[str, bytes, BinaryIO], filename: Optional[str] = None
) -> tuple[str, bytes]:
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
    return fn, content


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
        fn, content = _prepare_audio_file(file, filename)
        files = {"file": (fn, content)}
        data = {"diarize": str(diarize).lower()}
        res = self._transport.post_multipart("/v1/asr/transcribe/offline", files=files, data=data)
        return ASRResult.model_validate(res)

    def transcribe_job(
        self,
        file: Union[str, bytes, BinaryIO],
        diarize: bool = False,
        filename: Optional[str] = None,
    ) -> ASRJobAccepted:
        """
        Submit audio file for asynchronous transcription (HTTP 202).
        Poll status with client.asr.get_job(job_id) or client.asr.wait_for_job(job_id).
        """
        fn, content = _prepare_audio_file(file, filename)
        files = {"file": (fn, content)}
        data = {"diarize": str(diarize).lower()}
        res = self._transport.post_multipart("/v1/asr/transcribe/offline/jobs", files=files, data=data)
        return ASRJobAccepted.model_validate(res)

    def get_job(self, job_id: str) -> ASRJobStatus:
        """Poll the status and result of an async ASR transcription job."""
        res = self._transport.request("GET", f"/v1/asr/jobs/{job_id}")
        return ASRJobStatus.model_validate(res)

    def wait_for_job(
        self,
        job_or_file: Union[str, bytes, BinaryIO, ASRJobAccepted],
        diarize: bool = False,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> ASRJobStatus:
        """
        Convenience helper to submit or poll an async ASR job until completion.
        Accepts either an existing job_id / ASRJobAccepted instance, or audio bytes/file to enqueue and wait.
        """
        if isinstance(job_or_file, ASRJobAccepted):
            job_id = job_or_file.job_id
        elif isinstance(job_or_file, str) and not os.path.exists(job_or_file) and not job_or_file.endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm")):
            job_id = job_or_file
        else:
            job = self.transcribe_job(job_or_file, diarize=diarize)
            job_id = job.job_id

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_job(job_id)
            if status.status in ("completed", "done", "SUCCESS"):
                return status
            if status.status in ("failed", "error", "FAILURE"):
                raise RuntimeError(f"ASR Job {job_id} failed: {status.error}")
            time.sleep(poll_interval)
        raise TimeoutError(f"ASR Job {job_id} timed out after {timeout} seconds")

    def transcribe_youtube(
        self,
        url: str,
        include_audio: bool = True,
        diarize: bool = True,
    ) -> YouTubeASRResult:
        """Transcribe audio from a YouTube video URL synchronously."""
        payload = {
            "url": url,
            "include_audio": include_audio,
            "diarize": diarize,
        }
        res = self._transport.request("POST", "/v1/asr/transcribe/youtube", json=payload)
        return YouTubeASRResult.model_validate(res)

    def transcribe_youtube_job(
        self,
        url: str,
        include_audio: bool = True,
        diarize: bool = True,
    ) -> ASRJobAccepted:
        """Submit YouTube video for asynchronous transcription job."""
        payload = {
            "url": url,
            "include_audio": include_audio,
            "diarize": diarize,
        }
        res = self._transport.request("POST", "/v1/asr/transcribe/youtube/jobs", json=payload)
        return ASRJobAccepted.model_validate(res)

    def create_stream(
        self,
        sample_rate: int = 16000,
        diarization_enabled: bool = False,
        revision_enabled: bool = False,
    ) -> StreamSession:
        """Initiate a stateful live PCM16 speech recognition stream."""
        payload = {
            "sample_rate": sample_rate,
            "diarization_enabled": diarization_enabled,
            "revision_enabled": revision_enabled,
        }
        res = self._transport.request("POST", "/v1/asr/streams", json=payload, params={"sample_rate": sample_rate})
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
        url = f"/v1/asr/streams/{session_id}/chunk/pcm16"
        res = self._transport.request(
            "POST",
            url,
            content=pcm_bytes,
            params=params,
            headers=headers,
        )
        return StreamChunk.model_validate(res)

    def stream_chunk_json(
        self,
        session_id: str,
        audio_samples: List[Union[float, int]],
        sample_rate: int = 16000,
        encoding: str = "pcm16",
        generation: Optional[int] = None,
        chunk_sequence: Optional[int] = None,
    ) -> StreamChunk:
        """Submit audio samples as JSON float32 or pcm16 array."""
        payload: Dict[str, Any] = {
            "audio": audio_samples,
            "sample_rate": sample_rate,
            "encoding": encoding,
        }
        if generation is not None:
            payload["generation"] = generation
        if chunk_sequence is not None:
            payload["chunk_sequence"] = chunk_sequence

        res = self._transport.request("POST", f"/v1/asr/streams/{session_id}/chunk", json=payload)
        return StreamChunk.model_validate(res)

    def finish_stream(self, session_id: str) -> Dict[str, Any]:
        """Finalize live ASR stream and record usage."""
        return self._transport.request("POST", f"/v1/asr/streams/{session_id}/finish")

    def clear_stream(self, session_id: str) -> Dict[str, Any]:
        """Reset internal session buffer and advance generation."""
        return self._transport.request("POST", f"/v1/asr/streams/{session_id}/clear")

    def keepalive_stream(self, session_id: str) -> Dict[str, Any]:
        """Touch streaming session to reset inactivity TTL timer."""
        return self._transport.request("POST", f"/v1/asr/streams/{session_id}/keepalive")

    def abort_stream(self, session_id: str) -> None:
        """Abort and release streaming session."""
        self._transport.request("DELETE", f"/v1/asr/streams/{session_id}")


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
        """Synchronous audio file transcription with optional speaker diarization."""
        fn, content = _prepare_audio_file(file, filename)
        files = {"file": (fn, content)}
        data = {"diarize": str(diarize).lower()}
        res = await self._transport.post_multipart("/v1/asr/transcribe/offline", files=files, data=data)
        return ASRResult.model_validate(res)

    async def transcribe_job(
        self,
        file: Union[str, bytes, BinaryIO],
        diarize: bool = False,
        filename: Optional[str] = None,
    ) -> ASRJobAccepted:
        """Submit audio file for asynchronous transcription (HTTP 202)."""
        fn, content = _prepare_audio_file(file, filename)
        files = {"file": (fn, content)}
        data = {"diarize": str(diarize).lower()}
        res = await self._transport.post_multipart("/v1/asr/transcribe/offline/jobs", files=files, data=data)
        return ASRJobAccepted.model_validate(res)

    async def get_job(self, job_id: str) -> ASRJobStatus:
        """Poll the status and result of an async ASR transcription job."""
        res = await self._transport.request("GET", f"/v1/asr/jobs/{job_id}")
        return ASRJobStatus.model_validate(res)

    async def wait_for_job(
        self,
        job_or_file: Union[str, bytes, BinaryIO, ASRJobAccepted],
        diarize: bool = False,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> ASRJobStatus:
        """Convenience helper to submit or poll an async ASR job until completion."""
        if isinstance(job_or_file, ASRJobAccepted):
            job_id = job_or_file.job_id
        elif isinstance(job_or_file, str) and not os.path.exists(job_or_file) and not job_or_file.endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm")):
            job_id = job_or_file
        else:
            job = await self.transcribe_job(job_or_file, diarize=diarize)
            job_id = job.job_id

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = await self.get_job(job_id)
            if status.status in ("completed", "done", "SUCCESS"):
                return status
            if status.status in ("failed", "error", "FAILURE"):
                raise RuntimeError(f"ASR Job {job_id} failed: {status.error}")
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"ASR Job {job_id} timed out after {timeout} seconds")

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

    async def transcribe_youtube_job(
        self,
        url: str,
        include_audio: bool = True,
        diarize: bool = True,
    ) -> ASRJobAccepted:
        """Submit YouTube video for asynchronous transcription job."""
        payload = {
            "url": url,
            "include_audio": include_audio,
            "diarize": diarize,
        }
        res = await self._transport.request("POST", "/v1/asr/transcribe/youtube/jobs", json=payload)
        return ASRJobAccepted.model_validate(res)

    async def create_stream(
        self,
        sample_rate: int = 16000,
        diarization_enabled: bool = False,
        revision_enabled: bool = False,
    ) -> StreamSession:
        """Initiate a stateful live PCM16 speech recognition stream."""
        payload = {
            "sample_rate": sample_rate,
            "diarization_enabled": diarization_enabled,
            "revision_enabled": revision_enabled,
        }
        res = await self._transport.request("POST", "/v1/asr/streams", json=payload, params={"sample_rate": sample_rate})
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
        url = f"/v1/asr/streams/{session_id}/chunk/pcm16"
        res = await self._transport.request(
            "POST",
            url,
            content=pcm_bytes,
            params=params,
            headers=headers,
        )
        return StreamChunk.model_validate(res)

    async def stream_chunk_json(
        self,
        session_id: str,
        audio_samples: List[Union[float, int]],
        sample_rate: int = 16000,
        encoding: str = "pcm16",
        generation: Optional[int] = None,
        chunk_sequence: Optional[int] = None,
    ) -> StreamChunk:
        """Submit audio samples as JSON float32 or pcm16 array."""
        payload: Dict[str, Any] = {
            "audio": audio_samples,
            "sample_rate": sample_rate,
            "encoding": encoding,
        }
        if generation is not None:
            payload["generation"] = generation
        if chunk_sequence is not None:
            payload["chunk_sequence"] = chunk_sequence

        res = await self._transport.request("POST", f"/v1/asr/streams/{session_id}/chunk", json=payload)
        return StreamChunk.model_validate(res)

    async def finish_stream(self, session_id: str) -> Dict[str, Any]:
        """Finalize live ASR stream and record usage."""
        return await self._transport.request("POST", f"/v1/asr/streams/{session_id}/finish")

    async def clear_stream(self, session_id: str) -> Dict[str, Any]:
        """Reset internal session buffer and advance generation."""
        return await self._transport.request("POST", f"/v1/asr/streams/{session_id}/clear")

    async def keepalive_stream(self, session_id: str) -> Dict[str, Any]:
        """Touch streaming session to reset inactivity TTL timer."""
        return await self._transport.request("POST", f"/v1/asr/streams/{session_id}/keepalive")

    async def abort_stream(self, session_id: str) -> None:
        """Abort and release streaming session."""
        await self._transport.request("DELETE", f"/v1/asr/streams/{session_id}")
