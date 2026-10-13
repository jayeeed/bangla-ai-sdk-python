import asyncio
import os
import time
from typing import Any, AsyncGenerator, BinaryIO, Dict, Generator, List, Optional, Union

from .._base import AsyncTransport, SyncTransport
from ..types.tts import (
    CustomReferenceAudio,
    FrontendControls,
    TTSCapabilities,
    TTSDiscovery,
    TTSJobAccepted,
    TTSJobStatus,
    TTSQueueStatus,
    TTSSessionResponse,
    TTSVoiceUploadResponse,
)


def _prepare_audio_file(
    file: Union[str, bytes, BinaryIO], filename: Optional[str] = None
) -> tuple[str, bytes]:
    if isinstance(file, str):
        fn = filename or os.path.basename(file)
        with open(file, "rb") as f:
            content = f.read()
    elif isinstance(file, bytes):
        fn = filename or "voice_reference.wav"
        content = file
    else:
        fn = filename or getattr(file, "name", "voice_reference.wav")
        content = file.read()
    return fn, content


class TTSResource:
    """Operations for Speech Synthesis (Higgs TTS 3), voice cloning, and stateful streaming."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def synthesize(
        self,
        text: str,
        voice: str = "male",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
        first_segment_max_chars: int = 45,
    ) -> bytes:
        """
        Full-response voice synthesis returning complete audio/wav bytes.
        """
        payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "response_format": response_format,
            "first_segment_max_chars": first_segment_max_chars,
        }
        if voice_id:
            payload["voice_id"] = voice_id

        res = self._transport.request("POST", "/v1/tts/simple", json=payload)
        return res if isinstance(res, bytes) else str(res).encode("utf-8")

    def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "male",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
        first_segment_max_chars: int = 45,
    ) -> str:
        """Synthesize text and save directly to an audio file."""
        wav_bytes = self.synthesize(
            text,
            voice=voice,
            voice_id=voice_id,
            response_format=response_format,
            first_segment_max_chars=first_segment_max_chars,
        )
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        return output_path

    def stream_pcm(
        self,
        text: str,
        voice: str = "male",
        voice_id: Optional[str] = None,
        first_segment_max_chars: int = 45,
    ) -> Generator[bytes, None, None]:
        """Low-latency streamed 24 kHz mono signed 16-bit PCM bytes."""
        payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "first_segment_max_chars": first_segment_max_chars,
        }
        if voice_id:
            payload["voice_id"] = voice_id

        for chunk in self._transport.stream_bytes("/v1/tts/simple/stream", json_body=payload):
            yield chunk

    def advanced(
        self,
        input: str,
        voice: Optional[str] = "female",
        voice_id: Optional[str] = None,
        model: str = "bosonai/higgs-tts-3-4b",
        speed: float = 1.0,
        response_format: str = "wav",
        controls: Optional[Union[FrontendControls, Dict[str, Any]]] = None,
        custom_reference: Optional[Union[CustomReferenceAudio, Dict[str, Any]]] = None,
    ) -> bytes:
        """Advanced voice synthesis with custom zero-shot voice cloning and controls."""
        payload: Dict[str, Any] = {
            "model": model,
            "input": input,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
            "stream": False,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        if controls:
            payload["controls"] = controls.model_dump() if hasattr(controls, "model_dump") else controls
        if custom_reference:
            payload["custom_reference"] = custom_reference.model_dump() if hasattr(custom_reference, "model_dump") else custom_reference

        res = self._transport.request("POST", "/v1/tts/advanced", json=payload)
        return res if isinstance(res, bytes) else str(res).encode("utf-8")

    # --- Reusable Custom Voice Cloning ---
    def create_voice(
        self,
        file: Union[str, bytes, BinaryIO],
        name: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> TTSVoiceUploadResponse:
        """Upload a 3-10s reference audio sample to create a reusable voice profile."""
        fn, content = _prepare_audio_file(file, filename)
        files = {"file": (fn, content)}
        data = {}
        if name:
            data["name"] = name
        res = self._transport.post_multipart("/v1/tts/voices", files=files, data=data)
        return TTSVoiceUploadResponse.model_validate(res)

    def get_voice(self, voice_id: str) -> Dict[str, Any]:
        """Fetch metadata for an uploaded custom voice."""
        return self._transport.request("GET", f"/v1/tts/voices/{voice_id}")

    def delete_voice(self, voice_id: str) -> None:
        """Delete an uploaded custom voice profile."""
        self._transport.request("DELETE", f"/v1/tts/voices/{voice_id}")

    # --- Asynchronous Synthesis Jobs ---
    def create_job(
        self,
        text: str,
        voice: str = "default",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
    ) -> TTSJobAccepted:
        """Submit text for asynchronous synthesis (HTTP 202). Poll status with get_job()."""
        payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "response_format": response_format,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        res = self._transport.request("POST", "/v1/tts/simple/jobs", json=payload)
        return TTSJobAccepted.model_validate(res)

    def get_job(self, job_id: str) -> TTSJobStatus:
        """Poll the status and download URL of an async TTS synthesis job."""
        res = self._transport.request("GET", f"/v1/tts/jobs/{job_id}")
        return TTSJobStatus.model_validate(res)

    def download_job(self, job_id: str) -> bytes:
        """Download synthesized audio file bytes for a completed job."""
        res = self._transport.request("GET", f"/v1/tts/jobs/{job_id}/download")
        return res if isinstance(res, bytes) else str(res).encode("utf-8")

    def wait_for_job(
        self,
        job_or_text: Union[str, TTSJobAccepted],
        voice: str = "default",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> bytes:
        """
        Poll or submit an async TTS job until complete, then return the audio bytes.
        """
        if isinstance(job_or_text, TTSJobAccepted):
            job_id = job_or_text.job_id
        elif isinstance(job_or_text, str) and job_or_text.startswith("job_"):
            job_id = job_or_text
        else:
            job = self.create_job(job_or_text, voice=voice, voice_id=voice_id, response_format=response_format)
            job_id = job.job_id

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_job(job_id)
            if status.status in ("completed", "done", "SUCCESS"):
                return self.download_job(job_id)
            if status.status in ("failed", "error", "FAILURE"):
                raise RuntimeError(f"TTS Job {job_id} failed: {status.error}")
            time.sleep(poll_interval)
        raise TimeoutError(f"TTS Job {job_id} timed out after {timeout} seconds")

    # --- Stateful REST Text Streaming Sessions ---
    def create_session(
        self,
        voice: str = "default",
        voice_id: Optional[str] = None,
    ) -> TTSSessionResponse:
        """Create a stateful incremental text session for low-latency streaming."""
        payload: Dict[str, Any] = {"voice": voice}
        if voice_id:
            payload["voice_id"] = voice_id
        res = self._transport.request("POST", "/v1/tts/sessions", json=payload)
        return TTSSessionResponse.model_validate(res)

    def send_session_text(self, session_id: str, text: str) -> Dict[str, Any]:
        """Feed next incremental text delta into the session."""
        return self._transport.request("POST", f"/v1/tts/sessions/{session_id}/text", json={"text": text})

    def finish_session(self, session_id: str) -> Dict[str, Any]:
        """Signal completion of text stream to produce final audio segment."""
        return self._transport.request("POST", f"/v1/tts/sessions/{session_id}/finish")

    def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear pending text buffer in the session."""
        return self._transport.request("POST", f"/v1/tts/sessions/{session_id}/clear")

    def keepalive_session(self, session_id: str) -> Dict[str, Any]:
        """Keep session alive, resetting inactivity TTL timer."""
        return self._transport.request("POST", f"/v1/tts/sessions/{session_id}/keepalive")

    def delete_session(self, session_id: str) -> None:
        """Release session resources."""
        self._transport.request("DELETE", f"/v1/tts/sessions/{session_id}")

    # --- Discovery & Metadata ---
    def models(self) -> TTSDiscovery:
        """Discover available TTS models and default speaker voice presets."""
        res = self._transport.request("GET", "/v1/tts/models")
        return TTSDiscovery.model_validate(res)

    def list_voices(self) -> TTSDiscovery:
        """Alias for models() returning available speaker voice presets."""
        return self.models()

    def capabilities(self) -> TTSCapabilities:
        """Discover supported formats, profiles, voice cloning, and controls."""
        res = self._transport.request("GET", "/v1/capabilities")
        return TTSCapabilities.model_validate(res)

    def queue(self) -> TTSQueueStatus:
        """Inspect inference queue status, active jobs, and capacity limits."""
        res = self._transport.request("GET", "/v1/queue")
        return TTSQueueStatus.model_validate(res)


class AsyncTTSResource:
    """Asynchronous operations for Speech Synthesis (Higgs TTS 3)."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def synthesize(
        self,
        text: str,
        voice: str = "male",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
        first_segment_max_chars: int = 45,
    ) -> bytes:
        """Full-response voice synthesis returning complete audio/wav bytes."""
        payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "response_format": response_format,
            "first_segment_max_chars": first_segment_max_chars,
        }
        if voice_id:
            payload["voice_id"] = voice_id

        res = await self._transport.request("POST", "/v1/tts/simple", json=payload)
        return res if isinstance(res, bytes) else str(res).encode("utf-8")

    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: str = "male",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
        first_segment_max_chars: int = 45,
    ) -> str:
        """Synthesize text and save directly to an audio file."""
        wav_bytes = await self.synthesize(
            text,
            voice=voice,
            voice_id=voice_id,
            response_format=response_format,
            first_segment_max_chars=first_segment_max_chars,
        )
        with open(output_path, "wb") as f:
            f.write(wav_bytes)
        return output_path

    async def stream_pcm(
        self,
        text: str,
        voice: str = "male",
        voice_id: Optional[str] = None,
        first_segment_max_chars: int = 45,
    ) -> AsyncGenerator[bytes, None]:
        """Low-latency streamed 24 kHz mono signed 16-bit PCM bytes."""
        payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "first_segment_max_chars": first_segment_max_chars,
        }
        if voice_id:
            payload["voice_id"] = voice_id

        async for chunk in self._transport.stream_bytes("/v1/tts/simple/stream", json_body=payload):
            yield chunk

    async def advanced(
        self,
        input: str,
        voice: Optional[str] = "female",
        voice_id: Optional[str] = None,
        model: str = "bosonai/higgs-tts-3-4b",
        speed: float = 1.0,
        response_format: str = "wav",
        controls: Optional[Union[FrontendControls, Dict[str, Any]]] = None,
        custom_reference: Optional[Union[CustomReferenceAudio, Dict[str, Any]]] = None,
    ) -> bytes:
        """Advanced voice synthesis with custom zero-shot voice cloning and controls."""
        payload: Dict[str, Any] = {
            "model": model,
            "input": input,
            "voice": voice,
            "speed": speed,
            "response_format": response_format,
            "stream": False,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        if controls:
            payload["controls"] = controls.model_dump() if hasattr(controls, "model_dump") else controls
        if custom_reference:
            payload["custom_reference"] = custom_reference.model_dump() if hasattr(custom_reference, "model_dump") else custom_reference

        res = await self._transport.request("POST", "/v1/tts/advanced", json=payload)
        return res if isinstance(res, bytes) else str(res).encode("utf-8")

    async def create_voice(
        self,
        file: Union[str, bytes, BinaryIO],
        name: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> TTSVoiceUploadResponse:
        """Upload a 3-10s reference audio sample to create a reusable voice profile."""
        fn, content = _prepare_audio_file(file, filename)
        files = {"file": (fn, content)}
        data = {}
        if name:
            data["name"] = name
        res = await self._transport.post_multipart("/v1/tts/voices", files=files, data=data)
        return TTSVoiceUploadResponse.model_validate(res)

    async def get_voice(self, voice_id: str) -> Dict[str, Any]:
        """Fetch metadata for an uploaded custom voice."""
        return await self._transport.request("GET", f"/v1/tts/voices/{voice_id}")

    async def delete_voice(self, voice_id: str) -> None:
        """Delete an uploaded custom voice profile."""
        await self._transport.request("DELETE", f"/v1/tts/voices/{voice_id}")

    async def create_job(
        self,
        text: str,
        voice: str = "default",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
    ) -> TTSJobAccepted:
        """Submit text for asynchronous synthesis (HTTP 202)."""
        payload: Dict[str, Any] = {
            "text": text,
            "voice": voice,
            "response_format": response_format,
        }
        if voice_id:
            payload["voice_id"] = voice_id
        res = await self._transport.request("POST", "/v1/tts/simple/jobs", json=payload)
        return TTSJobAccepted.model_validate(res)

    async def get_job(self, job_id: str) -> TTSJobStatus:
        """Poll the status and download URL of an async TTS synthesis job."""
        res = await self._transport.request("GET", f"/v1/tts/jobs/{job_id}")
        return TTSJobStatus.model_validate(res)

    async def download_job(self, job_id: str) -> bytes:
        """Download synthesized audio file bytes for a completed job."""
        res = await self._transport.request("GET", f"/v1/tts/jobs/{job_id}/download")
        return res if isinstance(res, bytes) else str(res).encode("utf-8")

    async def wait_for_job(
        self,
        job_or_text: Union[str, TTSJobAccepted],
        voice: str = "default",
        voice_id: Optional[str] = None,
        response_format: str = "wav",
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> bytes:
        """Poll or submit an async TTS job until complete, then return the audio bytes."""
        if isinstance(job_or_text, TTSJobAccepted):
            job_id = job_or_text.job_id
        elif isinstance(job_or_text, str) and job_or_text.startswith("job_"):
            job_id = job_or_text
        else:
            job = await self.create_job(job_or_text, voice=voice, voice_id=voice_id, response_format=response_format)
            job_id = job.job_id

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = await self.get_job(job_id)
            if status.status in ("completed", "done", "SUCCESS"):
                return await self.download_job(job_id)
            if status.status in ("failed", "error", "FAILURE"):
                raise RuntimeError(f"TTS Job {job_id} failed: {status.error}")
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"TTS Job {job_id} timed out after {timeout} seconds")

    async def create_session(
        self,
        voice: str = "default",
        voice_id: Optional[str] = None,
    ) -> TTSSessionResponse:
        """Create a stateful incremental text session for low-latency streaming."""
        payload: Dict[str, Any] = {"voice": voice}
        if voice_id:
            payload["voice_id"] = voice_id
        res = await self._transport.request("POST", "/v1/tts/sessions", json=payload)
        return TTSSessionResponse.model_validate(res)

    async def send_session_text(self, session_id: str, text: str) -> Dict[str, Any]:
        """Feed next incremental text delta into the session."""
        return await self._transport.request("POST", f"/v1/tts/sessions/{session_id}/text", json={"text": text})

    async def finish_session(self, session_id: str) -> Dict[str, Any]:
        """Signal completion of text stream to produce final audio segment."""
        return await self._transport.request("POST", f"/v1/tts/sessions/{session_id}/finish")

    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear pending text buffer in the session."""
        return await self._transport.request("POST", f"/v1/tts/sessions/{session_id}/clear")

    async def keepalive_session(self, session_id: str) -> Dict[str, Any]:
        """Keep session alive, resetting inactivity TTL timer."""
        return await self._transport.request("POST", f"/v1/tts/sessions/{session_id}/keepalive")

    async def delete_session(self, session_id: str) -> None:
        """Release session resources."""
        await self._transport.request("DELETE", f"/v1/tts/sessions/{session_id}")

    async def models(self) -> TTSDiscovery:
        """Discover available TTS models and default speaker voice presets."""
        res = await self._transport.request("GET", "/v1/tts/models")
        return TTSDiscovery.model_validate(res)

    async def list_voices(self) -> TTSDiscovery:
        """Alias for models() returning available speaker voice presets."""
        return await self.models()

    async def capabilities(self) -> TTSCapabilities:
        """Discover supported formats, profiles, voice cloning, and controls."""
        res = await self._transport.request("GET", "/v1/capabilities")
        return TTSCapabilities.model_validate(res)

    async def queue(self) -> TTSQueueStatus:
        """Inspect inference queue status, active jobs, and capacity limits."""
        res = await self._transport.request("GET", "/v1/queue")
        return TTSQueueStatus.model_validate(res)
