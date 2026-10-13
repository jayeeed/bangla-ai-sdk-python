import pytest


def test_chat_lifecycle_and_streaming(mock_client):
    # 1. Create chat
    chat = mock_client.chats.create(
        title="Test Conversation",
        instructions="সহজ বাংলায় উত্তর দিন।"
    )
    assert chat.id == "cht_test123"
    assert chat.title == "Test Conversation"

    # 2. List & Get
    chats = mock_client.chats.list()
    assert len(chats) >= 1

    single_chat = mock_client.chats.get(chat.id)
    assert single_chat.id == chat.id

    # 3. Update chat
    updated = mock_client.chats.update(chat.id, title="Updated title")
    assert updated.title == "Updated title"

    # 4. Stream turn (asserting auto idempotency key)
    chunks = list(mock_client.chats.turns.stream(chat.id, content="হ্যালো"))
    assert len(chunks) >= 2
    tokens = [c.text for c in chunks if c.text]
    assert "".join(tokens) == "বাংলা এআই"

    # 5. Convenience non-streaming turn
    full_text = mock_client.chats.turns.create(chat.id, content="নমস্কার")
    assert full_text == "বাংলা এআই"
    assert full_text.content == "বাংলা এআই"
    assert full_text.turn_id == "trn_test123"

    # 6. Retrieve message history
    msgs = mock_client.chats.messages(chat.id)
    assert len(msgs) >= 1
    assert msgs[0].content == "নমস্কার! কিভাবে সাহায্য করতে পারি?"

    # 7. Create branch
    branched = mock_client.chats.create_branch(
        chat.id, source_branch_id="brn_test123", target_turn_id="trn_test123"
    )
    assert branched.active_branch_id == "brn_branch456"


def test_chat_attachments(mock_client):
    dummy_pdf_bytes = b"%PDF-1.4 dummy pdf data"
    att = mock_client.chats.attachments.upload("cht_test123", dummy_pdf_bytes, filename="sample.pdf")
    assert att.id == "att_test123"
    assert att.filename == "sample.pdf"

    downloaded = mock_client.chats.attachments.download("cht_test123", att.id)
    assert b"PDF" in downloaded

    # Delete attachment
    mock_client.chats.attachments.delete("cht_test123", att.id)
