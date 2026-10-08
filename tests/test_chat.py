import pytest


def test_chat_lifecycle_and_streaming(mock_client):
    # 1. Create chat
    chat = mock_client.chats.create(
        title="Test Conversation",
        instructions="সহজ বাংলায় উত্তর দিন।"
    )
    assert chat.id == "cht_test123"
    assert chat.title == "Test Conversation"

    # 2. List chats
    chats = mock_client.chats.list()
    assert len(chats) >= 1

    # 3. Stream turn
    chunks = list(mock_client.chats.turns.stream(chat.id, content="হ্যালো"))
    assert len(chunks) >= 2
    tokens = [c.text for c in chunks if c.text]
    assert "".join(tokens) == "বাংলা এআই"

    # 4. Convenience non-streaming turn
    full_text = mock_client.chats.turns.create(chat.id, content="নমস্কার")
    assert full_text == "বাংলা এআই"


def test_chat_attachments(mock_client):
    dummy_pdf_bytes = b"%PDF-1.4 dummy pdf data"
    att = mock_client.chats.attachments.upload("cht_test123", dummy_pdf_bytes, filename="sample.pdf")
    assert att.id == "att_test123"
    assert att.filename == "sample.pdf"

    downloaded = mock_client.chats.attachments.download("cht_test123", att.id)
    assert b"PDF" in downloaded
