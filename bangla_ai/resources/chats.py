import os
import uuid
from typing import Any, AsyncGenerator, BinaryIO, Dict, Generator, List, Optional, Union

from .._base import AsyncTransport, SyncTransport
from ..types.chat import Attachment, Chat, ChatProfile, Turn, TurnChunk


class TurnResult(str):
    """Aggregated turn result that acts as a string with metadata attributes."""

    text: str
    output_text: str
    content: str
    turn_id: Optional[str]
    branch_id: Optional[str]

    def __new__(cls, text: str, turn_id: Optional[str] = None, branch_id: Optional[str] = None) -> "TurnResult":
        instance = super().__new__(cls, text)
        instance.text = text
        instance.output_text = text
        instance.content = text
        instance.turn_id = turn_id
        instance.branch_id = branch_id
        return instance


class ChatTurnsResource:
    """Operations for conversation message turns within a chat."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def stream(
        self,
        chat_id: str,
        content: str,
        attachment_ids: Optional[List[str]] = None,
        branch_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Generator[TurnChunk, None, None]:
        """
        Stream assistant tokens chunk-by-chunk via Server-Sent Events (SSE).
        Automatically assigns an RFC 4122 Idempotency-Key header if not provided.
        """
        payload = {
            "content": content,
            "attachment_ids": attachment_ids or [],
            "branch_id": branch_id,
        }
        key = idempotency_key or str(uuid.uuid4())
        headers = {"Idempotency-Key": key}

        for chunk in self._transport.stream_sse(
            f"/v1/chats/{chat_id}/turns", json_body=payload, headers=headers
        ):
            event = chunk.get("event", "message")
            data = chunk.get("data", {})
            text = None
            turn_id = None
            branch_id_resp = None

            if isinstance(data, dict):
                text = data.get("text")
                turn_id = data.get("turn_id")
                branch_id_resp = data.get("branch_id")

            yield TurnChunk(
                event=event,
                text=text,
                turn_id=turn_id,
                branch_id=branch_id_resp,
                raw=data if isinstance(data, dict) else None,
            )

    def create(
        self,
        chat_id: str,
        content: str,
        attachment_ids: Optional[List[str]] = None,
        branch_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> TurnResult:
        """
        Convenience method to submit a turn, wait for completion, and return the aggregated response text.
        Returns a TurnResult where .content, .text, and str(turn) all yield the completed string.
        """
        tokens: List[str] = []
        last_turn_id: Optional[str] = None
        last_branch_id: Optional[str] = None

        for chunk in self.stream(
            chat_id,
            content=content,
            attachment_ids=attachment_ids,
            branch_id=branch_id,
            idempotency_key=idempotency_key,
        ):
            if chunk.text:
                tokens.append(chunk.text)
            if chunk.turn_id:
                last_turn_id = chunk.turn_id
            if chunk.branch_id:
                last_branch_id = chunk.branch_id

        full_text = "".join(tokens)
        return TurnResult(text=full_text, turn_id=last_turn_id, branch_id=last_branch_id)

    def cancel(self, chat_id: str, turn_id: str) -> Dict[str, Any]:
        """Cancel an ongoing streaming turn."""
        return self._transport.request("POST", f"/v1/chats/{chat_id}/turns/{turn_id}/cancel")


class AsyncChatTurnsResource:
    """Asynchronous operations for conversation message turns within a chat."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def stream(
        self,
        chat_id: str,
        content: str,
        attachment_ids: Optional[List[str]] = None,
        branch_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> AsyncGenerator[TurnChunk, None]:
        """
        Stream assistant tokens chunk-by-chunk via Server-Sent Events (SSE).
        """
        payload = {
            "content": content,
            "attachment_ids": attachment_ids or [],
            "branch_id": branch_id,
        }
        key = idempotency_key or str(uuid.uuid4())
        headers = {"Idempotency-Key": key}

        async for chunk in self._transport.stream_sse(
            f"/v1/chats/{chat_id}/turns", json_body=payload, headers=headers
        ):
            event = chunk.get("event", "message")
            data = chunk.get("data", {})
            text = None
            turn_id = None
            branch_id_resp = None

            if isinstance(data, dict):
                text = data.get("text")
                turn_id = data.get("turn_id")
                branch_id_resp = data.get("branch_id")

            yield TurnChunk(
                event=event,
                text=text,
                turn_id=turn_id,
                branch_id=branch_id_resp,
                raw=data if isinstance(data, dict) else None,
            )

    async def create(
        self,
        chat_id: str,
        content: str,
        attachment_ids: Optional[List[str]] = None,
        branch_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> TurnResult:
        """
        Convenience method to submit a turn, wait for completion, and return the aggregated response text.
        """
        tokens: List[str] = []
        last_turn_id: Optional[str] = None
        last_branch_id: Optional[str] = None

        async for chunk in self.stream(
            chat_id,
            content=content,
            attachment_ids=attachment_ids,
            branch_id=branch_id,
            idempotency_key=idempotency_key,
        ):
            if chunk.text:
                tokens.append(chunk.text)
            if chunk.turn_id:
                last_turn_id = chunk.turn_id
            if chunk.branch_id:
                last_branch_id = chunk.branch_id

        full_text = "".join(tokens)
        return TurnResult(text=full_text, turn_id=last_turn_id, branch_id=last_branch_id)

    async def cancel(self, chat_id: str, turn_id: str) -> Dict[str, Any]:
        """Cancel an ongoing streaming turn."""
        return await self._transport.request("POST", f"/v1/chats/{chat_id}/turns/{turn_id}/cancel")


class ChatAttachmentsResource:
    """Operations for MinIO-stored attachments linked to a chat."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def upload(self, chat_id: str, file: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> Attachment:
        """Upload a document (PDF) or image (PNG, JPEG) attachment to MinIO."""
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "attachment.bin"
            content = file
        else:
            fn = filename or getattr(file, "name", "attachment.bin")
            content = file.read()

        files = {"file": (fn, content)}
        res = self._transport.post_multipart(f"/v1/chats/{chat_id}/attachments", files=files)
        return Attachment.model_validate(res)

    def list(self, chat_id: str) -> List[Attachment]:
        """List all attachments associated with a chat session."""
        res = self._transport.request("GET", f"/v1/chats/{chat_id}/attachments")
        return [Attachment.model_validate(item) for item in res]

    def get(self, chat_id: str, attachment_id: str) -> Attachment:
        """Fetch metadata for a single chat attachment."""
        res = self._transport.request("GET", f"/v1/chats/{chat_id}/attachments/{attachment_id}")
        return Attachment.model_validate(res)

    def download(self, chat_id: str, attachment_id: str) -> bytes:
        """Download raw binary bytes of a stored attachment."""
        return self._transport.request("GET", f"/v1/chats/{chat_id}/attachments/{attachment_id}/download")

    def delete(self, chat_id: str, attachment_id: str) -> None:
        """Delete an attachment from MinIO and detach from the chat."""
        self._transport.request("DELETE", f"/v1/chats/{chat_id}/attachments/{attachment_id}")


class AsyncChatAttachmentsResource:
    """Asynchronous operations for MinIO-stored attachments linked to a chat."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def upload(self, chat_id: str, file: Union[str, bytes, BinaryIO], filename: Optional[str] = None) -> Attachment:
        """Upload a document (PDF) or image (PNG, JPEG) attachment to MinIO."""
        if isinstance(file, str):
            fn = filename or os.path.basename(file)
            with open(file, "rb") as f:
                content = f.read()
        elif isinstance(file, bytes):
            fn = filename or "attachment.bin"
            content = file
        else:
            fn = filename or getattr(file, "name", "attachment.bin")
            content = file.read()

        files = {"file": (fn, content)}
        res = await self._transport.post_multipart(f"/v1/chats/{chat_id}/attachments", files=files)
        return Attachment.model_validate(res)

    async def list(self, chat_id: str) -> List[Attachment]:
        """List all attachments associated with a chat session."""
        res = await self._transport.request("GET", f"/v1/chats/{chat_id}/attachments")
        return [Attachment.model_validate(item) for item in res]

    async def get(self, chat_id: str, attachment_id: str) -> Attachment:
        """Fetch metadata for a single chat attachment."""
        res = await self._transport.request("GET", f"/v1/chats/{chat_id}/attachments/{attachment_id}")
        return Attachment.model_validate(res)

    async def download(self, chat_id: str, attachment_id: str) -> bytes:
        """Download raw binary bytes of a stored attachment."""
        return await self._transport.request("GET", f"/v1/chats/{chat_id}/attachments/{attachment_id}/download")

    async def delete(self, chat_id: str, attachment_id: str) -> None:
        """Delete an attachment from MinIO and detach from the chat."""
        await self._transport.request("DELETE", f"/v1/chats/{chat_id}/attachments/{attachment_id}")


class ChatsResource:
    """Operations for conversational LLM chat threads and turns."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport
        self.turns = ChatTurnsResource(transport)
        self.attachments = ChatAttachmentsResource(transport)

    def create(
        self,
        title: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: bool = False,
        profile: Optional[ChatProfile] = None,
    ) -> Chat:
        """Create a new conversational session thread."""
        chat_profile = profile or ChatProfile(
            instructions=instructions or "",
            enable_web_search=enable_web_search,
        )
        payload = {
            "title": title,
            "profile": chat_profile.model_dump(),
        }
        res = self._transport.request("POST", "/v1/chats", json=payload)
        return Chat.model_validate(res)

    def list(self, limit: int = 50, offset: int = 0) -> List[Chat]:
        """List user's active conversation threads."""
        res = self._transport.request("GET", "/v1/chats", params={"limit": limit, "offset": offset})
        return [Chat.model_validate(item) for item in res]

    def get(self, chat_id: str) -> Chat:
        """Fetch details of a single conversation thread."""
        res = self._transport.request("GET", f"/v1/chats/{chat_id}")
        return Chat.model_validate(res)

    def update(
        self,
        chat_id: str,
        title: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: Optional[bool] = None,
    ) -> Chat:
        """Update conversation title or instructions."""
        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if instructions is not None or enable_web_search is not None:
            profile_data: Dict[str, Any] = {}
            if instructions is not None:
                profile_data["instructions"] = instructions
            if enable_web_search is not None:
                profile_data["enable_web_search"] = enable_web_search
            payload["profile"] = profile_data

        res = self._transport.request("PATCH", f"/v1/chats/{chat_id}", json=payload)
        return Chat.model_validate(res)

    def delete(self, chat_id: str) -> None:
        """Delete / archive a conversation thread."""
        self._transport.request("DELETE", f"/v1/chats/{chat_id}")

    def messages(self, chat_id: str) -> List[Turn]:
        """Retrieve full message turn history for a chat."""
        res = self._transport.request("GET", f"/v1/chats/{chat_id}/messages")
        return [Turn.model_validate(item) for item in res]

    def create_branch(
        self,
        chat_id: str,
        source_branch_id: str,
        target_turn_id: str,
        action: str = "regenerate",
        edited_content: Optional[str] = None,
    ) -> Chat:
        """Fork conversation history into a new branch."""
        payload = {
            "source_branch_id": source_branch_id,
            "target_turn_id": target_turn_id,
            "action": action,
            "edited_content": edited_content,
        }
        res = self._transport.request("POST", f"/v1/chats/{chat_id}/branches", json=payload)
        return Chat.model_validate(res)


class AsyncChatsResource:
    """Asynchronous operations for conversational LLM chat threads and turns."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport
        self.turns = AsyncChatTurnsResource(transport)
        self.attachments = AsyncChatAttachmentsResource(transport)

    async def create(
        self,
        title: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: bool = False,
        profile: Optional[ChatProfile] = None,
    ) -> Chat:
        """Create a new conversational session thread."""
        chat_profile = profile or ChatProfile(
            instructions=instructions or "",
            enable_web_search=enable_web_search,
        )
        payload = {
            "title": title,
            "profile": chat_profile.model_dump(),
        }
        res = await self._transport.request("POST", "/v1/chats", json=payload)
        return Chat.model_validate(res)

    async def list(self, limit: int = 50, offset: int = 0) -> List[Chat]:
        """List user's active conversation threads."""
        res = await self._transport.request("GET", "/v1/chats", params={"limit": limit, "offset": offset})
        return [Chat.model_validate(item) for item in res]

    async def get(self, chat_id: str) -> Chat:
        """Fetch details of a single conversation thread."""
        res = await self._transport.request("GET", f"/v1/chats/{chat_id}")
        return Chat.model_validate(res)

    async def update(
        self,
        chat_id: str,
        title: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: Optional[bool] = None,
    ) -> Chat:
        """Update conversation title or instructions."""
        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if instructions is not None or enable_web_search is not None:
            profile_data: Dict[str, Any] = {}
            if instructions is not None:
                profile_data["instructions"] = instructions
            if enable_web_search is not None:
                profile_data["enable_web_search"] = enable_web_search
            payload["profile"] = profile_data

        res = await self._transport.request("PATCH", f"/v1/chats/{chat_id}", json=payload)
        return Chat.model_validate(res)

    async def delete(self, chat_id: str) -> None:
        """Delete / archive a conversation thread."""
        await self._transport.request("DELETE", f"/v1/chats/{chat_id}")

    async def messages(self, chat_id: str) -> List[Turn]:
        """Retrieve full message turn history for a chat."""
        res = await self._transport.request("GET", f"/v1/chats/{chat_id}/messages")
        return [Turn.model_validate(item) for item in res]

    async def create_branch(
        self,
        chat_id: str,
        source_branch_id: str,
        target_turn_id: str,
        action: str = "regenerate",
        edited_content: Optional[str] = None,
    ) -> Chat:
        """Fork conversation history into a new branch."""
        payload = {
            "source_branch_id": source_branch_id,
            "target_turn_id": target_turn_id,
            "action": action,
            "edited_content": edited_content,
        }
        res = await self._transport.request("POST", f"/v1/chats/{chat_id}/branches", json=payload)
        return Chat.model_validate(res)
