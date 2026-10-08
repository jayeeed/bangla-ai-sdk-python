import asyncio
import os
import time
from typing import BinaryIO, Optional, Union
from urllib.parse import quote
from .._base import AsyncTransport, SyncTransport
from ..exceptions import BanglaAIError
from ..types.ocr import OCRJob, OCRResult


class OCRResource:
    """Operations for Document OCR (single page & multi-page async batch)."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def process(self, file: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> OCRResult:
        """
        Synchronous document OCR for single-page documents and images.
        Returns layout regions, pages, and extracted Bengali Markdown.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "document.jpg"
            content = file
        else:
            fn = filename or getattr(file, "name", "document.jpg")
            content = file.read()

        files = {"file": (fn, content)}
        data = self._transport.post_multipart("/v1/ocr", files=files)
        return OCRResult.model_validate(data)

    def create_job(self, file: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> OCRJob:
        """
        Asynchronously submits a multi-page document or batch for OCR processing.
        Returns an OCRJob with status 'queued'.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "document.pdf"
            content = file
        else:
            fn = filename or getattr(file, "name", "document.pdf")
            content = file.read()

        files = {"file": (fn, content)}
        data = self._transport.post_multipart("/v1/ocr/jobs", files=files)
        return OCRJob.model_validate(data)

    def get_job(self, job_id: str) -> OCRJob:
        """Poll status and retrieve result of an asynchronous Document OCR job."""
        data = self._transport.request("GET", f"/v1/ocr/jobs/{quote(str(job_id), safe='')}")
        return OCRJob.model_validate(data)

    def wait_for_job(
        self,
        job_or_file: Union[str, bytes, BinaryIO, OCRJob],
        filename: Optional[str] = None,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> OCRJob:
        """
        Submits (if given a file) and automatically polls the OCR job until it completes or fails.
        """
        if isinstance(job_or_file, OCRJob):
            job_id = job_or_file.job_id
        elif isinstance(job_or_file, str) and job_or_file.startswith("job_"):
            job_id = job_or_file
        else:
            job = self.create_job(job_or_file, filename=filename)
            job_id = job.job_id

        if not job_id:
            raise BanglaAIError("Failed to initiate OCR job: response did not include a valid job_id.")

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_job(job_id)
            if status.status == "completed":
                return status
            elif status.status == "failed":
                raise BanglaAIError(f"OCR job {job_id} failed: {status.error or 'Unknown error'}")
            time.sleep(poll_interval)

        raise TimeoutError(f"OCR job {job_id} did not finish within {timeout} seconds.")


class AsyncOCRResource:
    """Asynchronous operations for Document OCR (single page & multi-page async batch)."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def process(self, file: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> OCRResult:
        """
        Synchronous document OCR for single-page documents and images.
        Returns layout regions, pages, and extracted Bengali Markdown.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "document.jpg"
            content = file
        else:
            fn = filename or getattr(file, "name", "document.jpg")
            content = file.read()

        files = {"file": (fn, content)}
        data = await self._transport.post_multipart("/v1/ocr", files=files)
        return OCRResult.model_validate(data)

    async def create_job(self, file: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> OCRJob:
        """
        Asynchronously submits a multi-page document or batch for OCR processing.
        Returns an OCRJob with status 'queued'.
        """
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "document.pdf"
            content = file
        else:
            fn = filename or getattr(file, "name", "document.pdf")
            content = file.read()

        files = {"file": (fn, content)}
        data = await self._transport.post_multipart("/v1/ocr/jobs", files=files)
        return OCRJob.model_validate(data)

    async def get_job(self, job_id: str) -> OCRJob:
        """Poll status and retrieve result of an asynchronous Document OCR job."""
        data = await self._transport.request("GET", f"/v1/ocr/jobs/{quote(str(job_id), safe='')}")
        return OCRJob.model_validate(data)

    async def wait_for_job(
        self,
        job_or_file: Union[str, bytes, BinaryIO, OCRJob],
        filename: Optional[str] = None,
        timeout: float = 300.0,
        poll_interval: float = 2.0,
    ) -> OCRJob:
        """
        Submits (if given a file) and automatically polls the OCR job until it completes or fails.
        """
        if isinstance(job_or_file, OCRJob):
            job_id = job_or_file.job_id
        elif isinstance(job_or_file, str) and job_or_file.startswith("job_"):
            job_id = job_or_file
        else:
            job = await self.create_job(job_or_file, filename=filename)
            job_id = job.job_id

        if not job_id:
            raise BanglaAIError("Failed to initiate OCR job: response did not include a valid job_id.")

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = await self.get_job(job_id)
            if status.status == "completed":
                return status
            elif status.status == "failed":
                raise BanglaAIError(f"OCR job {job_id} failed: {status.error or 'Unknown error'}")
            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"OCR job {job_id} did not finish within {timeout} seconds.")
