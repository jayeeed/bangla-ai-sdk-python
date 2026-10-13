import pytest


def test_offline_asr(mock_client):
    audio_bytes = b"RIFFmockwavcontent"
    res = mock_client.asr.transcribe(audio_bytes, diarize=True, filename="speech.wav")
    assert res.text == "পরীক্ষামূলক বাংলা ভয়েস অডিও।"
    assert res.duration_seconds == 2.5


def test_asr_async_job_and_wait(mock_client):
    audio_bytes = b"RIFFmockwavcontent"
    job = mock_client.asr.transcribe_job(audio_bytes, diarize=True)
    assert job.job_id == "job_asr123"
    assert job.status == "queued"

    status = mock_client.asr.get_job(job.job_id)
    assert status.status == "completed"
    assert "অ্যাসিঙ্ক" in status.result["text"]

    waited = mock_client.asr.wait_for_job(job)
    assert waited.status == "completed"


def test_youtube_asr(mock_client):
    res = mock_client.asr.transcribe_youtube("https://youtube.com/watch?v=123")
    assert res.text == "ইউটিউব ভিডিওর ট্রান্সক্রিপ্ট।"
    assert res.title == "ভিডিও শিরোনাম"

    job = mock_client.asr.transcribe_youtube_job("https://youtube.com/watch?v=123")
    assert job.job_id == "job_yt123"


def test_streaming_asr(mock_client):
    session = mock_client.asr.create_stream(sample_rate=16000)
    assert session.session_id == "str_asr123"

    chunk = mock_client.asr.stream_chunk(session.session_id, b"\x00" * 3200)
    assert chunk.transcript == "বাংলা লাইভ"
    assert chunk.partial_text == "লাইভ"

    cleared = mock_client.asr.clear_stream(session.session_id)
    assert cleared["status"] == "cleared"

    alive = mock_client.asr.keepalive_stream(session.session_id)
    assert alive["status"] == "ok"

    finish = mock_client.asr.finish_stream(session.session_id)
    assert finish["status"] == "finished"
