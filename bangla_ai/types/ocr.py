from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OCRRegion(BaseModel):
    model_config = ConfigDict(extra="ignore")

    box_2d: List[int]
    label: str
    text: str


class OCRPage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    page_number: int
    width: int
    height: int
    markdown: str
    regions: List[OCRRegion] = Field(default_factory=list)


class OCRTiming(BaseModel):
    model_config = ConfigDict(extra="ignore")

    total_elapsed_ms: float = 0.0
    ocr_ms: Optional[float] = 0.0
    layout_ms: Optional[float] = 0.0


class OCRResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    markdown: str
    pages: List[OCRPage] = Field(default_factory=list)
    timing: Optional[OCRTiming] = None


class OCRJob(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[OCRResult] = None
    status_url: Optional[str] = None
    queue_depth: Optional[int] = None


class OCRJobAccepted(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    status: str = "queued"
    status_url: str
    queue_depth: int = 0
