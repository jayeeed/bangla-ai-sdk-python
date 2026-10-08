from typing import List, Optional
from pydantic import BaseModel, Field


class TTSDiscovery(BaseModel):
    models: List[str] = Field(default_factory=list)
    voices: List[str] = Field(default_factory=list)
    default_voice: str = "male"
    sample_rate: int = 24000


class CustomReferenceAudio(BaseModel):
    audio_base64: str
    transcript: str
