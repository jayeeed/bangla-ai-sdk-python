from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OCRRegion(BaseModel):
    box_2d: List[int]
    label: str
    text: str


class OCRPage(BaseModel):
    page_number: int
    width: int
    height: int
    markdown: str
    regions: List[OCRRegion] = Field(default_factory=list)


class OCRTiming(BaseModel):
    total_elapsed_ms: float = 0.0
    ocr_ms: Optional[float] = 0.0
    layout_ms: Optional[float] = 0.0


class OCRResult(BaseModel):
    markdown: str
    pages: List[OCRPage] = Field(default_factory=list)
    timing: Optional[OCRTiming] = None


class OCRJob(BaseModel):
    job_id: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[OCRResult] = None
    status_url: Optional[str] = None
    queue_depth: Optional[int] = None
