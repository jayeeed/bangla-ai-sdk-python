from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TTSDiscovery(BaseModel):
    model_config = ConfigDict(extra="ignore")

    models: List[str] = Field(default_factory=list)
    voices: List[str] = Field(default_factory=list)
    speakers: List[str] = Field(default_factory=list)
    default_voice: str = "male"
    sample_rate: int = 24000
    response_formats: List[str] = Field(default_factory=lambda: ["wav", "mp3", "flac", "opus", "aac", "pcm"])

    def get(self, key: str, default: Any = None) -> Any:
        val = getattr(self, key, default)
        return val if val is not None else default

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class TTSCapabilities(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object: str = "tts_capabilities"
    model: str = "bosonai/higgs-tts-3-4b"
    backend_contract: Optional[str] = "openai-compatible"
    default_reference_speaker: Optional[str] = "female"
    response_formats: List[str] = Field(default_factory=lambda: ["wav", "mp3", "flac", "opus", "aac", "pcm"])
    speaking_speed: List[str] = Field(default_factory=lambda: ["very_slow", "slow", "normal", "fast", "very_fast"])
    streaming: bool = True
    rest_text_sessions: bool = True
    voice_cloning: bool = True


class TTSQueueStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object: str = "tts_queue"
    active: int = 0
    queued: int = 0
    capacity: int = 4
    available: int = 4


class TTSVoiceUploadResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    voice_id: str
    status: str = "ready"
    reference_text: Optional[str] = ""
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = 24000
    channels: Optional[int] = 1
    denoise: Optional[bool] = True
    processing: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class TTSSessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    object: str = "tts_session"
    session_id: str
    status: str = "open"
    text_url: Optional[str] = None
    finish_url: Optional[str] = None
    audio_format: Optional[str] = "pcm_s16le"
    sample_rate: Optional[int] = 24000
    channels: Optional[int] = 1
    bit_depth: Optional[int] = 16
    ttl_seconds: Optional[float] = 900.0


class TTSJobAccepted(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str = "queued"
    status_url: str


class TTSJobStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
    size_bytes: Optional[int] = None
    format: Optional[str] = None


class FrontendControls(BaseModel):
    model_config = ConfigDict(extra="ignore")

    emotion: Optional[str] = None
    style: Optional[str] = None
    sound_effect: Optional[str] = None
    sound_effect_text: Optional[str] = None


class CustomReferenceAudio(BaseModel):
    model_config = ConfigDict(extra="ignore")

    audio_base64: Optional[str] = None
    audio_url: Optional[str] = None
    transcript: Optional[str] = None
