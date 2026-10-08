from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ASRResult(BaseModel):
    text: str
    mode: str = "offline"
    status: str = "done"
    processing: bool = False
    done: bool = True
    request_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
    duration_seconds: Optional[float] = None


class YouTubeASRResult(BaseModel):
    text: str
    title: Optional[str] = None
    duration_seconds: Optional[float] = None
    source_url: str
    audio_download_url: Optional[str] = None
    diarization_text: Optional[str] = None
    diarization: Optional[List[Dict[str, Any]]] = None


class StreamSession(BaseModel):
    session_id: str
    sample_rate: int = 16000


class StreamChunk(BaseModel):
    transcript: str
    partial_text: str
    final_text: str = ""
    final_words: List[Dict[str, Any]] = Field(default_factory=list)
    event: str = "partial"
    turn_id: Optional[str] = None
