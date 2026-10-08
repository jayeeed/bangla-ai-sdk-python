from typing import Optional
from pydantic import BaseModel


class VoiceReference(BaseModel):
    reference_id: str
    transcript: Optional[str] = None


class LiveKitToken(BaseModel):
    url: str
    token: str
    room: str

    @property
    def room_name(self) -> str:
        return self.room

    @property
    def livekit_url(self) -> str:
        return self.url
