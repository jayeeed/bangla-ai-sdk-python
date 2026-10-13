import pytest


def test_tts_synthesis(mock_client, tmp_path):
    # 1. Models & Voices
    models = mock_client.tts.models()
    assert "bosonai/higgs-tts-3-4b" in models.models
    assert "male" in models.voices

    voices = mock_client.tts.list_voices()
    assert len(voices.voices) >= 2

    # 1b. Capabilities & Queue
    caps = mock_client.tts.capabilities()
    assert caps.streaming is True
    assert caps.voice_cloning is True

    q = mock_client.tts.queue()
    assert q.capacity == 4
    assert q.available == 4

    # 2. Synthesize bytes
    wav_bytes = mock_client.tts.synthesize("স্বাগতম!", voice="female")
    assert wav_bytes.startswith(b"RIFF")

    # 3. Synthesize to file
    out_file = str(tmp_path / "test.wav")
    saved_path = mock_client.tts.synthesize_to_file("স্বাগতম!", out_file)
    assert saved_path == out_file

    # 4. Stream PCM
    chunks = list(mock_client.tts.stream_pcm("লাইভ অডিও"))
    assert len(chunks) >= 1
    assert b"\x00" in chunks[0]

    # 5. Voice profile upload
    voice_resp = mock_client.tts.create_voice(b"RIFFvoicebytes", name="TestVoice")
    assert voice_resp.voice_id.startswith("voice_hex")
    assert voice_resp.status == "ready"

    # 6. Async synthesis job & wait
    job = mock_client.tts.create_job("অ্যাসিঙ্ক টেক্সট")
    assert job.job_id == "job_tts123"
    job_status = mock_client.tts.get_job(job.job_id)
    assert job_status.status == "completed"

    job_audio = mock_client.tts.wait_for_job(job)
    assert job_audio.startswith(b"RIFF")

    # 7. Incremental streaming session
    session = mock_client.tts.create_session(voice="male")
    assert session.session_id == "sess_tts123"
    assert session.status == "open"
    mock_client.tts.send_session_text(session.session_id, "হ্যালো")
    mock_client.tts.finish_session(session.session_id)
    mock_client.tts.delete_session(session.session_id)
