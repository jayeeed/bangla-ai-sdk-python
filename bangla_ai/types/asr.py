from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ASRResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str
    mode: str = "offline"
    status: Optional[str] = "done"
    processing: bool = False
    done: bool = True
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
    duration_seconds: Optional[float] = None
    diarization: Optional[List[Dict[str, Any]]] = None
    diarization_text: Optional[str] = None
    diarization_enabled: Optional[bool] = None


class YouTubeASRResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    text: str
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    source_url: str
    audio_download_url: Optional[str] = None
    mode: str = "offline"
    diarization_text: Optional[str] = None
    diarization: Optional[List[Dict[str, Any]]] = None
    diarization_enabled: Optional[bool] = None
    processing: bool = False
    done: bool = True
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None


class StreamSession(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: str
    sample_rate: int = 16000
    generation: int = 0
    processing: bool = False
    done: bool = False
    diarization_enabled: bool = False
    revision_enabled: bool = False


class StreamChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    session_id: Optional[str] = None
    transcript: str = ""
    partial_text: str = ""
    final_text: str = ""
    segment_partial_text: str = ""
    segment_text: str = ""
    segment_committed: bool = False
    final_words: List[Dict[str, Any]] = Field(default_factory=list)
    event: str = "partial"
    turn_id: Optional[str] = None
    sequence: int = 0
    generation: int = 0
    is_final: bool = False
    diarization: Optional[List[Dict[str, Any]]] = None
    diarization_text: Optional[str] = None
    speaker_transcript_segments: Optional[List[Dict[str, Any]]] = None


class ASRJobAccepted(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str = "queued"
    status_url: str


class ASRJobStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
