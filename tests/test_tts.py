import pytest


def test_tts_synthesis(mock_client, tmp_path):
    # 1. Models
    models = mock_client.tts.models()
    assert "bosonai/higgs-tts-3-4b" in models.models
    assert "male" in models.voices

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
