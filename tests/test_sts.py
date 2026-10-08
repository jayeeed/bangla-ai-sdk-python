import pytest


def test_sts_voice_reference_and_token(mock_client):
    # 1. Upload reference
    ref = mock_client.sts.upload_voice_reference(b"RIFFmockwavcontent", filename="my_voice.wav")
    assert ref.reference_id == "spk_ref123"
    assert ref.transcript == "নমুনা ভয়েস ক্লিপ"

    # 2. Get LiveKit token
    token = mock_client.sts.get_livekit_token(reference_id=ref.reference_id)
    assert token.url == "wss://livekit.bangla-ai.org"
    assert token.room == "room_test123"
    assert "mock_jwt_token" in token.token

    # 3. Test alias create_token
    token_alias = mock_client.sts.create_token(reference_id=ref.reference_id)
    assert token_alias.room == "room_test123"


@pytest.mark.asyncio
async def test_async_sts(mock_async_client):
    ref = await mock_async_client.sts.upload_voice_reference(b"RIFFmockwavcontent", filename="my_voice.wav")
    assert ref.reference_id == "spk_ref123"

    token = await mock_async_client.sts.get_livekit_token(reference_id=ref.reference_id)
    assert token.room == "room_test123"
