from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    instructions: Optional[str] = ""
    enable_web_search: bool = False
    custom_tool_names: List[str] = Field(default_factory=list)


class Chat(BaseModel):
    """Conversation thread model."""
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: Optional[str] = None
    title: str = "New session"
    primary_service: str = "llm"
    is_archived: bool = False
    active_branch_id: Optional[str] = None
    context_state: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Turn(BaseModel):
    """Conversation message turn."""
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    branch_id: Optional[str] = None
    service: str = "llm"
    input_modality: str = "text"
    output_modality: str = "text"
    input_content: str = ""
    input_attachment_ids: List[str] = Field(default_factory=list)
    output_text: str = ""
    output_items: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Dict[str, Any] = Field(default_factory=dict)
    status: str = "completed"
    error_code: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def content(self) -> str:
        return self.output_text or self.input_content


class TurnChunk(BaseModel):
    """Streaming chunk from an active turn SSE stream."""
    model_config = ConfigDict(extra="ignore")

    event: str
    text: Optional[str] = None
    turn_id: Optional[str] = None
    branch_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class Attachment(BaseModel):
    """Chat file attachment metadata."""
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    service: str = "llm"
    kind: str = "document"
    filename: str
    content_type: str
    size_bytes: int
    storage_key: Optional[str] = None
    sha256: Optional[str] = None
    is_attached: bool = True
    download_url: Optional[str] = None
    created_at: Optional[datetime] = None


class ChatBranch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    chat_id: str
    parent_branch_id: Optional[str] = None
    fork_after_turn_id: Optional[str] = None
    created_at: Optional[datetime] = None
