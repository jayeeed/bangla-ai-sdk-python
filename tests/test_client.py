import pytest
import httpx
from bangla_ai import BanglaAI, AuthenticationError, NotFoundError
from .conftest import mock_handler


def test_client_init_and_health(mock_client):
    health = mock_client.health()
    assert health["status"] == "ok"
    assert health["service"] == "Bangla AI Gateway"

    ready = mock_client.ready()
    assert ready["status"] == "healthy"
    assert ready["checks"]["database"] == "ok"


def test_auth_error_on_missing_key():
    client = BanglaAI(api_key=None)
    mock_transport = httpx.MockTransport(mock_handler)
    client._transport._client = httpx.Client(
        base_url=client._transport.config.base_url,
        transport=mock_transport,
    )
    with pytest.raises(AuthenticationError) as exc_info:
        client.me.get()
    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "MISSING_AUTHENTICATION"


def test_user_profile_and_update(mock_client):
    profile = mock_client.me.get()
    assert profile.id == "usr_test123"
    assert profile.email == "test@bangla-ai.org"
    assert profile.role == "developer"

    updated = mock_client.me.update(display_name="New Name")
    assert updated.display_name == "New Name"


def test_api_keys_crud(mock_client):
    new_key = mock_client.api_keys.create(name="My Integration Key", scopes=["llm", "ocr"])
    assert new_key.id == "key_test123"
    assert new_key.name == "My Integration Key"
    assert new_key.raw_api_key == "sk_live_test_raw_key_123"

    keys = mock_client.api_keys.list()
    assert len(keys) >= 1
    assert keys[0].id == "key_test123"

    # Delete
    mock_client.api_keys.delete("key_test123")


def test_ws_ticket(mock_client):
    ticket = mock_client.ws_tickets.create(target="asr_call")
    assert ticket.ticket == "tkt_sample123"
    assert ticket.target == "asr_call"
    assert ticket.ttl_seconds == 30
