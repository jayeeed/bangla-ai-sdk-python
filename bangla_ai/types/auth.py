from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile information returned by the gateway."""
    id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    role: str = "user"
    plan: str = "free"
    is_active: bool = True
    service_permissions: Dict[str, Any] = Field(default_factory=dict)
    firebase_uid: Optional[str] = None
    created_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class ApiKey(BaseModel):
    """Developer API key metadata."""
    id: str
    user_id: str
    name: str
    key_prefix: str
    scopes: List[str] = Field(default_factory=list)
    rate_limit_tier: str = "developer_free"
    is_active: bool = True
    allowed_ips: List[str] = Field(default_factory=list)
    allowed_origins: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    raw_api_key: Optional[str] = None


class WsTicket(BaseModel):
    """Single-use ticket for authenticating WebSockets."""
    ticket: str
    target: str
    stream_session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    ttl_seconds: int = 30
