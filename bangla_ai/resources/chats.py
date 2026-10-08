import os
from typing import Any, AsyncGenerator, BinaryIO, Dict, Generator, List, Optional, Union
from urllib.parse import quote
from .._base import AsyncTransport, SyncTransport
from ..types.chat import Attachment, Chat, ChatProfile, Turn, TurnChunk


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
    ) -> Generator[TurnChunk, None, None]:
        """
        Stream assistant tokens chunk-by-chunk via Server-Sent Events (SSE).
        Yields TurnChunk instances.
        """
        payload = {
            "content": content,
            "attachment_ids": attachment_ids or [],
            "branch_id": branch_id,
        }
        for chunk in self._transport.stream_sse(f"/v1/chats/{quote(str(chat_id), safe='')}/turns", json_body=payload):
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
    ) -> str:
        """
        Convenience method to submit a turn, wait for completion, and return the aggregated response text.
        """
        tokens = []
        for chunk in self.stream(chat_id, content=content, attachment_ids=attachment_ids, branch_id=branch_id):
            if chunk.text:
                tokens.append(chunk.text)
        return "".join(tokens)

    def cancel(self, chat_id: str, turn_id: str) -> Dict[str, Any]:
        """Cancel an ongoing streaming turn."""
        return self._transport.request("POST", f"/v1/chats/{quote(str(chat_id), safe='')}/turns/{quote(str(turn_id), safe='')}/cancel")


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
    ) -> AsyncGenerator[TurnChunk, None]:
        """
        Stream assistant tokens chunk-by-chunk via Server-Sent Events (SSE).
        """
        payload = {
            "content": content,
            "attachment_ids": attachment_ids or [],
            "branch_id": branch_id,
        }
        async for chunk in self._transport.stream_sse(f"/v1/chats/{quote(str(chat_id), safe='')}/turns", json_body=payload):
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
    ) -> str:
        """
        Convenience method to submit a turn, wait for completion, and return the aggregated response text.
        """
        tokens = []
        async for chunk in self.stream(chat_id, content=content, attachment_ids=attachment_ids, branch_id=branch_id):
            if chunk.text:
                tokens.append(chunk.text)
        return "".join(tokens)

    async def cancel(self, chat_id: str, turn_id: str) -> Dict[str, Any]:
        """Cancel an ongoing streaming turn."""
        return await self._transport.request("POST", f"/v1/chats/{quote(str(chat_id), safe='')}/turns/{quote(str(turn_id), safe='')}/cancel")


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
            fn = filename or "file.bin"
            content = file
        else:
            fn = filename or getattr(file, "name", "file.bin")
            content = file.read()

        files = {"file": (fn, content)}
        data = self._transport.post_multipart(f"/v1/chats/{quote(str(chat_id), safe='')}/attachments", files=files)
        return Attachment.model_validate(data)

    def list(self, chat_id: str) -> List[Attachment]:
        """List all attachments pinned to this chat thread."""
        data = self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments")
        return [Attachment.model_validate(item) for item in data]

    def get(self, chat_id: str, attachment_id: str) -> Attachment:
        """Fetch metadata for a specific chat attachment."""
        data = self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments/{quote(str(attachment_id), safe='')}")
        return Attachment.model_validate(data)

    def download(self, chat_id: str, attachment_id: str) -> bytes:
        """Download binary file content from MinIO object storage."""
        return self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments/{quote(str(attachment_id), safe='')}/download")

    def delete(self, chat_id: str, attachment_id: str) -> None:
        """Delete an attachment from MinIO and database."""
        self._transport.request("DELETE", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments/{quote(str(attachment_id), safe='')}")


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
            fn = filename or "file.bin"
            content = file
        else:
            fn = filename or getattr(file, "name", "file.bin")
            content = file.read()

        files = {"file": (fn, content)}
        data = await self._transport.post_multipart(f"/v1/chats/{quote(str(chat_id), safe='')}/attachments", files=files)
        return Attachment.model_validate(data)

    async def list(self, chat_id: str) -> List[Attachment]:
        """List all attachments pinned to this chat thread."""
        data = await self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments")
        return [Attachment.model_validate(item) for item in data]

    async def get(self, chat_id: str, attachment_id: str) -> Attachment:
        """Fetch metadata for a specific chat attachment."""
        data = await self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments/{quote(str(attachment_id), safe='')}")
        return Attachment.model_validate(data)

    async def download(self, chat_id: str, attachment_id: str) -> bytes:
        """Download binary file content from MinIO object storage."""
        return await self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments/{quote(str(attachment_id), safe='')}/download")

    async def delete(self, chat_id: str, attachment_id: str) -> None:
        """Delete an attachment from MinIO and database."""
        await self._transport.request("DELETE", f"/v1/chats/{quote(str(chat_id), safe='')}/attachments/{quote(str(attachment_id), safe='')}")


class ChatsResource:
    """Operations for multi-modal, multi-branch conversation threads."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport
        self.turns = ChatTurnsResource(transport)
        self.attachments = ChatAttachmentsResource(transport)

    def create(
        self,
        title: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: bool = False,
        custom_tool_names: Optional[List[str]] = None,
    ) -> Chat:
        """Initiate a new multi-branch LLM chat session."""
        profile = ChatProfile(
            instructions=instructions or "",
            enable_web_search=enable_web_search,
            custom_tool_names=custom_tool_names or [],
        )
        payload = {"title": title, "profile": profile.model_dump()}
        data = self._transport.request("POST", "/v1/chats", json=payload)
        return Chat.model_validate(data)

    def list(self) -> List[Chat]:
        """List active conversation threads."""
        data = self._transport.request("GET", "/v1/chats")
        return [Chat.model_validate(item) for item in data]

    def get(self, chat_id: str) -> Chat:
        """Retrieve chat session details and active branch ID."""
        data = self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}")
        return Chat.model_validate(data)

    def update(
        self,
        chat_id: str,
        title: Optional[str] = None,
        is_archived: Optional[bool] = None,
        context_state: Optional[Dict[str, Any]] = None,
    ) -> Chat:
        """Update chat title, archive flag, or system context."""
        payload = {}
        if title is not None:
            payload["title"] = title
        if is_archived is not None:
            payload["is_archived"] = is_archived
        if context_state is not None:
            payload["context_state"] = context_state

        data = self._transport.request("PATCH", f"/v1/chats/{quote(str(chat_id), safe='')}", json=payload)
        return Chat.model_validate(data)

    def delete(self, chat_id: str) -> None:
        """Delete chat thread and all related branches and turns."""
        self._transport.request("DELETE", f"/v1/chats/{quote(str(chat_id), safe='')}")

    def messages(self, chat_id: str, branch_id: Optional[str] = None) -> List[Turn]:
        """List chronological conversation turns along the active or specified branch."""
        params = {}
        if branch_id:
            params["branch_id"] = branch_id
        data = self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/messages", params=params)
        return [Turn.model_validate(item) for item in data]

    def create_branch(
        self,
        chat_id: str,
        source_branch_id: str,
        action: str = "edit",
        target_turn_id: Optional[str] = None,
        edited_content: Optional[str] = None,
    ) -> Chat:
        """Fork conversation tree into a new branch from a prior turn."""
        payload = {
            "source_branch_id": source_branch_id,
            "action": action,
            "target_turn_id": target_turn_id,
            "edited_content": edited_content,
        }
        data = self._transport.request("POST", f"/v1/chats/{quote(str(chat_id), safe='')}/branches", json=payload)
        return Chat.model_validate(data)


class AsyncChatsResource:
    """Asynchronous operations for multi-modal, multi-branch conversation threads."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport
        self.turns = AsyncChatTurnsResource(transport)
        self.attachments = AsyncChatAttachmentsResource(transport)

    async def create(
        self,
        title: Optional[str] = None,
        instructions: Optional[str] = None,
        enable_web_search: bool = False,
        custom_tool_names: Optional[List[str]] = None,
    ) -> Chat:
        """Initiate a new multi-branch LLM chat session."""
        profile = ChatProfile(
            instructions=instructions or "",
            enable_web_search=enable_web_search,
            custom_tool_names=custom_tool_names or [],
        )
        payload = {"title": title, "profile": profile.model_dump()}
        data = await self._transport.request("POST", "/v1/chats", json=payload)
        return Chat.model_validate(data)

    async def list(self) -> List[Chat]:
        """List active conversation threads."""
        data = await self._transport.request("GET", "/v1/chats")
        return [Chat.model_validate(item) for item in data]

    async def get(self, chat_id: str) -> Chat:
        """Retrieve chat session details and active branch ID."""
        data = await self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}")
        return Chat.model_validate(data)

    async def update(
        self,
        chat_id: str,
        title: Optional[str] = None,
        is_archived: Optional[bool] = None,
        context_state: Optional[Dict[str, Any]] = None,
    ) -> Chat:
        """Update chat title, archive flag, or system context."""
        payload = {}
        if title is not None:
            payload["title"] = title
        if is_archived is not None:
            payload["is_archived"] = is_archived
        if context_state is not None:
            payload["context_state"] = context_state

        data = await self._transport.request("PATCH", f"/v1/chats/{quote(str(chat_id), safe='')}", json=payload)
        return Chat.model_validate(data)

    async def delete(self, chat_id: str) -> None:
        """Delete chat thread and all related branches and turns."""
        await self._transport.request("DELETE", f"/v1/chats/{quote(str(chat_id), safe='')}")

    async def messages(self, chat_id: str, branch_id: Optional[str] = None) -> List[Turn]:
        """List chronological conversation turns along the active or specified branch."""
        params = {}
        if branch_id:
            params["branch_id"] = branch_id
        data = await self._transport.request("GET", f"/v1/chats/{quote(str(chat_id), safe='')}/messages", params=params)
        return [Turn.model_validate(item) for item in data]

    async def create_branch(
        self,
        chat_id: str,
        source_branch_id: str,
        action: str = "edit",
        target_turn_id: Optional[str] = None,
        edited_content: Optional[str] = None,
    ) -> Chat:
        """Fork conversation tree into a new branch from a prior turn."""
        payload = {
            "source_branch_id": source_branch_id,
            "action": action,
            "target_turn_id": target_turn_id,
            "edited_content": edited_content,
        }
        data = await self._transport.request("POST", f"/v1/chats/{quote(str(chat_id), safe='')}/branches", json=payload)
        return Chat.model_validate(data)
