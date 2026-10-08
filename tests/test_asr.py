import pytest


def test_offline_asr(mock_client):
    audio_bytes = b"RIFFmockwavcontent"
    res = mock_client.asr.transcribe(audio_bytes, diarize=True, filename="speech.wav")
    assert res.text == "পরীক্ষামূলক বাংলা ভয়েস অডিও।"
    assert res.duration_seconds == 2.5


def test_youtube_asr(mock_client):
    res = mock_client.asr.transcribe_youtube("https://youtube.com/watch?v=123")
    assert res.text == "ইউটিউব ভিডিওর ট্রান্সক্রিপ্ট।"
    assert res.title == "ভিডিও শিরোনাম"


def test_streaming_asr(mock_client):
    session = mock_client.asr.create_stream(sample_rate=16000)
    assert session.session_id == "str_asr123"

    chunk = mock_client.asr.stream_chunk(session.session_id, b"\x00" * 3200)
    assert chunk.transcript == "বাংলা লাইভ"
    assert chunk.partial_text == "লাইভ"

    finish = mock_client.asr.finish_stream(session.session_id)
    assert finish["status"] == "finished"
