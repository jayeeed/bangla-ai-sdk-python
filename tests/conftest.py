import json
import pytest
import httpx
from bangla_ai import BanglaAI, AsyncBanglaAI
from bangla_ai._base import _BaseConfig, SyncTransport, AsyncTransport


def mock_handler(request: httpx.Request) -> httpx.Response:
    url_path = request.url.path
    method = request.method

    # Auth check
    auth_header = request.headers.get("authorization")
    api_key_header = request.headers.get("x-api-key")
    if not (auth_header or api_key_header):
        return httpx.Response(
            401,
            json={
                "type": "https://banglai.acimisai.com/errors/unauthorized",
                "title": "Unauthorized",
                "status": 401,
                "code": "MISSING_AUTHENTICATION",
                "detail": "Missing API key or Bearer token.",
            },
        )

    # 1. System probes
    if url_path == "/healthz":
        return httpx.Response(200, json={"status": "ok", "service": "Bangla AI Gateway", "version": "2.0.0"})
    if url_path == "/readyz":
        return httpx.Response(200, json={"status": "healthy", "checks": {"database": "ok", "redis": "ok"}})

    # 2. User profile
    if url_path == "/v1/me" and method == "GET":
        return httpx.Response(200, json={
            "id": "usr_test123",
            "email": "test@bangla-ai.org",
            "display_name": "Test User",
            "role": "developer",
            "plan": "developer_pro",
            "is_active": True,
            "service_permissions": {"allowed_scopes": ["llm", "ocr", "asr", "tts", "sts"]},
        })
    if url_path == "/v1/me" and method == "PATCH":
        body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={
            "id": "usr_test123",
            "email": "test@bangla-ai.org",
            "display_name": body.get("display_name", "Updated User"),
            "role": "developer",
            "plan": "developer_pro",
            "is_active": True,
        })

    # 2b. Auth / Google sync
    if url_path in ("/v1/auth/google", "/auth/google", "/google") and method == "POST":
        return httpx.Response(200, json={
            "status": "synced",
            "user": {
                "id": "usr_test123",
                "email": "google_user@test.org",
                "display_name": "Google User",
                "role": "user",
                "plan": "free",
                "is_active": True,
            },
            "synced": True,
            "provider": "google",
            "tier": "free",
            "scopes": ["llm", "ocr", "asr", "tts", "sts"],
        })

    # 3. API Keys
    if url_path == "/v1/api-keys" and method == "POST":
        body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(201, json={
            "id": "key_test123",
            "user_id": "usr_test123",
            "name": body.get("name", "test-key"),
            "key_prefix": "bgai_live_1234",
            "scopes": body.get("scopes", ["llm"]),
            "rate_limit_tier": "developer_free",
            "is_active": True,
            "raw_api_key": "sk_live_test_raw_key_123",
        })
    if url_path == "/v1/api-keys" and method == "GET":
        return httpx.Response(200, json=[{
            "id": "key_test123",
            "user_id": "usr_test123",
            "name": "test-key",
            "key_prefix": "bgai_live_1234",
            "scopes": ["llm"],
            "rate_limit_tier": "developer_free",
            "is_active": True,
        }])
    if url_path.startswith("/v1/api-keys/") and method == "DELETE":
        return httpx.Response(204)

    # 4. WebSocket ticket
    if url_path == "/v1/ws/tickets" and method == "POST":
        body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(201, json={
            "ticket": "tkt_sample123",
            "target": body.get("target", "asr_call"),
            "stream_session_id": body.get("stream_session_id"),
            "ttl_seconds": 30,
        })

    # 5. Chats
    if url_path == "/v1/chats" and method == "POST":
        body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(201, json={
            "id": "cht_test123",
            "user_id": "usr_test123",
            "title": body.get("title", "New session"),
            "primary_service": "llm",
            "is_archived": False,
            "active_branch_id": "brn_test123",
            "context_state": body.get("profile", {}),
        })
    if url_path == "/v1/chats" and method == "GET":
        return httpx.Response(200, json=[{
            "id": "cht_test123",
            "user_id": "usr_test123",
            "title": "New session",
            "primary_service": "llm",
            "is_archived": False,
            "active_branch_id": "brn_test123",
        }])
    if url_path == "/v1/chats/cht_test123" and method == "GET":
        return httpx.Response(200, json={
            "id": "cht_test123",
            "user_id": "usr_test123",
            "title": "New session",
            "primary_service": "llm",
            "is_archived": False,
            "active_branch_id": "brn_test123",
        })
    if url_path == "/v1/chats/cht_test123" and method == "PATCH":
        body = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={
            "id": "cht_test123",
            "user_id": "usr_test123",
            "title": body.get("title", "Updated title"),
            "primary_service": "llm",
            "is_archived": False,
            "active_branch_id": "brn_test123",
        })
    if url_path == "/v1/chats/cht_test123/messages" and method == "GET":
        return httpx.Response(200, json=[{
            "id": "trn_test123",
            "user_id": "usr_test123",
            "chat_id": "cht_test123",
            "input_content": "নমস্কার",
            "output_text": "নমস্কার! কিভাবে সাহায্য করতে পারি?",
            "status": "completed",
        }])
    if url_path == "/v1/chats/cht_test123/branches" and method == "POST":
        return httpx.Response(200, json={
            "id": "cht_test123",
            "user_id": "usr_test123",
            "title": "New session",
            "active_branch_id": "brn_branch456",
        })
    if url_path.endswith("/turns") and method == "POST":
        # Check idempotency key header
        assert "idempotency-key" in request.headers
        sse_content = (
            "event: turn_started\n"
            "data: {\"turn_id\": \"trn_test123\", \"branch_id\": \"brn_test123\"}\n\n"
            "event: token\n"
            "data: {\"text\": \"বাংলা \"}\n\n"
            "event: token\n"
            "data: {\"text\": \"এআই\"}\n\n"
            "event: turn_completed\n"
            "data: {\"turn_id\": \"trn_test123\", \"status\": \"completed\"}\n\n"
        )
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, content=sse_content.encode("utf-8"))

    if "/attachments" in url_path and method == "POST":
        return httpx.Response(201, json={
            "id": "att_test123",
            "user_id": "usr_test123",
            "chat_id": "cht_test123",
            "service": "llm",
            "kind": "document",
            "filename": "sample.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024,
            "storage_key": "attachments/att_test123/sample.pdf",
            "is_attached": True,
        })
    if "/attachments/" in url_path and method == "DELETE":
        return httpx.Response(204)
    if "/attachments/" in url_path and "/download" in url_path and method == "GET":
        return httpx.Response(200, content=b"%PDF-1.4 mock binary pdf bytes", headers={"Content-Type": "application/pdf"})

    # 6. OCR
    if url_path == "/v1/ocr" and method == "POST":
        return httpx.Response(200, json={
            "markdown": "# নমুনা নথি\nএটি একটি পরীক্ষা।",
            "pages": [{"page_number": 1, "width": 800, "height": 600, "markdown": "# নমুনা নথি", "regions": []}],
            "timing": {"total_elapsed_ms": 120.0},
        })
    if url_path == "/v1/ocr/jobs" and method == "POST":
        return httpx.Response(202, json={
            "job_id": "job_ocr123",
            "status": "queued",
            "status_url": "/v1/ocr/jobs/job_ocr123",
            "queue_depth": 1,
        })
    if url_path == "/v1/ocr/jobs/job_ocr123" and method == "GET":
        return httpx.Response(200, json={
            "job_id": "job_ocr123",
            "status": "completed",
            "result": {"markdown": "# সম্পূর্ণ নথি", "pages": []},
        })

    # 7. ASR
    if url_path == "/v1/asr/transcribe/offline" and method == "POST":
        return httpx.Response(200, json={
            "text": "পরীক্ষামূলক বাংলা ভয়েস অডিও।",
            "mode": "offline",
            "status": "done",
            "duration_seconds": 2.5,
            "processing_time_ms": 310.0,
        })
    if url_path == "/v1/asr/transcribe/offline/jobs" and method == "POST":
        return httpx.Response(202, json={
            "job_id": "job_asr123",
            "status": "queued",
            "status_url": "/v1/asr/jobs/job_asr123",
        })
    if url_path == "/v1/asr/jobs/job_asr123" and method == "GET":
        return httpx.Response(200, json={
            "job_id": "job_asr123",
            "status": "completed",
            "result": {"text": "অ্যাসিঙ্ক এএসআর ফলাফল।"},
        })
    if url_path == "/v1/asr/transcribe/youtube" and method == "POST":
        return httpx.Response(200, json={
            "text": "ইউটিউব ভিডিওর ট্রান্সক্রিপ্ট।",
            "title": "ভিডিও শিরোনাম",
            "duration_seconds": 60.0,
            "source_url": "https://youtube.com/watch?v=123",
        })
    if url_path == "/v1/asr/transcribe/youtube/jobs" and method == "POST":
        return httpx.Response(202, json={
            "job_id": "job_yt123",
            "status": "queued",
            "status_url": "/v1/asr/jobs/job_yt123",
        })
    if url_path in ("/v1/asr/streams", "/v1/asr/stream/start") and method == "POST":
        return httpx.Response(200, json={"session_id": "str_asr123", "sample_rate": 16000})
    if "/chunk/pcm16" in url_path and method == "POST":
        return httpx.Response(200, json={
            "transcript": "বাংলা লাইভ",
            "partial_text": "লাইভ",
            "final_text": "বাংলা ",
            "event": "partial",
        })
    if url_path.endswith("/finish") and method == "POST":
        return httpx.Response(200, json={"status": "finished", "session_id": "str_asr123"})
    if url_path.endswith("/clear") and method == "POST":
        return httpx.Response(200, json={"status": "cleared", "session_id": "str_asr123"})
    if url_path.endswith("/keepalive") and method == "POST":
        return httpx.Response(200, json={"status": "ok", "session_id": "str_asr123"})

    # 8. TTS
    if url_path == "/v1/tts/simple" and method == "POST":
        return httpx.Response(200, content=b"RIFFmockwavcontent", headers={"Content-Type": "audio/wav"})
    if url_path == "/v1/tts/simple/stream" and method == "POST":
        return httpx.Response(200, content=b"\x00\x01\x00\x02\x00\x03", headers={"Content-Type": "application/octet-stream"})
    if url_path in ("/v1/tts/models", "/v1/models") and method == "GET":
        return httpx.Response(200, json={"models": ["bosonai/higgs-tts-3-4b"], "voices": ["male", "female"], "default_voice": "male", "sample_rate": 24000})
    if url_path in ("/v1/capabilities", "/v1/tts/capabilities") and method == "GET":
        return httpx.Response(200, json={
            "object": "tts_capabilities",
            "model": "bosonai/higgs-tts-3-4b",
            "streaming": True,
            "voice_cloning": True,
            "response_formats": ["wav", "mp3", "pcm"],
        })
    if url_path in ("/v1/queue", "/v1/tts/queue") and method == "GET":
        return httpx.Response(200, json={
            "object": "tts_queue",
            "active": 0,
            "queued": 0,
            "capacity": 4,
            "available": 4,
        })
    if url_path == "/v1/tts/voices" and method == "POST":
        return httpx.Response(201, json={
            "voice_id": "voice_hex1234567890abcdef12345678",
            "status": "ready",
            "duration_seconds": 4.2,
        })
    if url_path.startswith("/v1/tts/voices/") and method == "GET":
        return httpx.Response(200, json={"voice_id": "voice_hex123", "status": "ready"})
    if url_path.startswith("/v1/tts/voices/") and method == "DELETE":
        return httpx.Response(204)
    if url_path == "/v1/tts/simple/jobs" and method == "POST":
        return httpx.Response(202, json={
            "job_id": "job_tts123",
            "status": "queued",
            "status_url": "/v1/tts/jobs/job_tts123",
        })
    if url_path == "/v1/tts/jobs/job_tts123" and method == "GET":
        return httpx.Response(200, json={
            "job_id": "job_tts123",
            "status": "completed",
            "download_url": "/v1/tts/jobs/job_tts123/download",
            "format": "wav",
        })
    if url_path == "/v1/tts/jobs/job_tts123/download" and method == "GET":
        return httpx.Response(200, content=b"RIFFmockjobaudiowavbytes", headers={"Content-Type": "audio/wav"})
    if url_path == "/v1/tts/sessions" and method == "POST":
        return httpx.Response(200, json={
            "object": "tts_session",
            "session_id": "sess_tts123",
            "status": "open",
            "text_url": "/v1/tts/sessions/sess_tts123/text",
            "finish_url": "/v1/tts/sessions/sess_tts123/finish",
        })
    if "/tts/sessions/" in url_path and method in ("POST", "DELETE"):
        return httpx.Response(200, json={"status": "ok"})

    # 9. STS
    if url_path == "/v1/sts/voice/reference" and method == "POST":
        return httpx.Response(200, json={"reference_id": "spk_ref123", "transcript": "নমুনা ভয়েস ক্লিপ"})
    if url_path == "/v1/sts/livekit/token" and method == "POST":
        return httpx.Response(200, json={"url": "wss://livekit.bangla-ai.org", "token": "mock_jwt_token_123", "room": "room_test123"})

    # Fallback 404
    return httpx.Response(404, json={"detail": f"Not found: {url_path}"})


@pytest.fixture
def mock_client():
    """Returns a BanglaAI client connected to a mock transport."""
    client = BanglaAI(api_key="sk_live_test_api_key_valid")
    config = client._transport.config
    mock_transport = httpx.MockTransport(mock_handler)
    client._transport._client = httpx.Client(
        base_url=config.base_url,
        headers=config.get_headers(),
        transport=mock_transport,
    )
    yield client
    client.close()


@pytest.fixture
def mock_async_client():
    """Returns an AsyncBanglaAI client connected to a mock transport."""
    client = AsyncBanglaAI(api_key="sk_live_test_api_key_valid")
    config = client._transport.config
    mock_transport = httpx.MockTransport(mock_handler)
    client._transport._client = httpx.AsyncClient(
        base_url=config.base_url,
        headers=config.get_headers(),
        transport=mock_transport,
    )
    return client
