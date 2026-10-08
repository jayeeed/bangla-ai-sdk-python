import pytest


def test_sync_ocr(mock_client):
    dummy_img = b"\xff\xd8\xff\xe0mock_jpeg_bytes"
    res = mock_client.ocr.process(dummy_img, filename="test.jpg")
    assert "# নমুনা নথি" in res.markdown
    assert len(res.pages) == 1
    assert res.pages[0].width == 800


def test_async_ocr_job(mock_client):
    dummy_pdf = b"%PDF-1.4 mock pdf"
    job = mock_client.ocr.create_job(dummy_pdf, filename="contract.pdf")
    assert job.job_id == "job_ocr123"
    assert job.status == "queued"

    completed_job = mock_client.ocr.wait_for_job(job.job_id, poll_interval=0.1)
    assert completed_job.status == "completed"
    assert completed_job.result is not None
    assert "# সম্পূর্ণ নথি" in completed_job.result.markdown
