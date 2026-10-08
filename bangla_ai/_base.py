import asyncio
import json
import os
import time
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional, Tuple, Union
import httpx

from ._constants import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, USER_AGENT
from .exceptions import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamServiceError,
)


def _handle_error_response(response: httpx.Response) -> None:
    """Parses RFC 7807 problem details and raises the appropriate typed exception."""
    status_code = response.status_code
    if status_code < 400:
        return

    request_id = response.headers.get("X-Request-ID")
    code = "UNKNOWN_ERROR"
    detail = response.text
    response_body = {}

    try:
        body = response.json()
        if isinstance(body, dict):
            response_body = body
            code = body.get("code", code)
            detail = body.get("detail") or body.get("message") or response.text
    except Exception:
        pass

    retry_after: Optional[int] = None
    if "Retry-After" in response.headers:
        try:
            retry_after = int(response.headers["Retry-After"])
        except ValueError:
            pass

    if status_code == 400:
        raise BadRequestError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)
    elif status_code == 401:
        raise AuthenticationError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)
    elif status_code == 403:
        raise PermissionDeniedError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)
    elif status_code == 404:
        raise NotFoundError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)
    elif status_code == 429:
        raise RateLimitError(detail, status_code=status_code, code=code, request_id=request_id, retry_after=retry_after, response_body=response_body)
    elif status_code == 500:
        raise InternalServerError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)
    elif status_code == 502:
        raise UpstreamServiceError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)
    elif status_code == 503:
        raise ServiceUnavailableError(detail, status_code=status_code, code=code, request_id=request_id, retry_after=retry_after, response_body=response_body)
    else:
        raise APIStatusError(detail, status_code=status_code, code=code, request_id=request_id, response_body=response_body)


class _BaseConfig:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("BANGLA_AI_API_KEY")
        self.base_url = (base_url or os.getenv("BANGLA_AI_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.custom_headers = headers or {}

    def get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            **self.custom_headers,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        return headers


class SyncTransport:
    """Synchronous HTTP transport engine using httpx.Client."""

    def __init__(self, config: _BaseConfig) -> None:
        self.config = config
        self._client = httpx.Client(
            base_url=self.config.base_url,
            headers=self.config.get_headers(),
            timeout=self.config.timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        retries = 0
        while True:
            try:
                resp = self._client.request(method, url, json=json, params=params, headers=headers)
                if (resp.status_code == 429 or resp.status_code == 503) and retries < self.config.max_retries:
                    retries += 1
                    retry_after_hdr = resp.headers.get("Retry-After")
                    try:
                        delay = float(retry_after_hdr) if retry_after_hdr else 0.5 * (2 ** (retries - 1))
                    except ValueError:
                        delay = 0.5 * (2 ** (retries - 1))
                    time.sleep(delay)
                    continue

                _handle_error_response(resp)
                if resp.status_code == 204:
                    return None
                content_type = resp.headers.get("content-type", "")
                if "application/json" in content_type:
                    return resp.json()
                return resp.content
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                if retries < self.config.max_retries:
                    retries += 1
                    time.sleep(0.5 * (2 ** (retries - 1)))
                    continue
                raise APIConnectionError(f"Connection failed to {url}: {str(exc)}") from exc

    def post_multipart(
        self,
        path: str,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        try:
            resp = self._client.post(url, files=files, data=data, params=params)
            _handle_error_response(resp)
            if resp.status_code == 204:
                return None
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                return resp.json()
            return resp.content
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise APIConnectionError(f"Connection failed to {url}: {str(exc)}") from exc

    def stream_sse(
        self,
        path: str,
        json_body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        headers = {"Accept": "text/event-stream"}
        try:
            with self._client.stream("POST", url, json=json_body, params=params, headers=headers) as resp:
                _handle_error_response(resp)
                current_event = "message"
                data_lines = []
                for line in resp.iter_lines():
                    trimmed = line.strip()
                    if not trimmed:
                        if data_lines:
                            data_str = "\n".join(data_lines)
                            try:
                                parsed_data = json.loads(data_str)
                            except Exception:
                                parsed_data = data_str
                            yield {"event": current_event, "data": parsed_data}
                            current_event = "message"
                            data_lines = []
                        continue
                    if trimmed.startswith(":"):
                        continue
                    if trimmed.startswith("event:"):
                        current_event = trimmed[6:].strip()
                    elif trimmed.startswith("data:"):
                        data_lines.append(trimmed[5:].strip())
                if data_lines:
                    data_str = "\n".join(data_lines)
                    try:
                        parsed_data = json.loads(data_str)
                    except Exception:
                        parsed_data = data_str
                    yield {"event": current_event, "data": parsed_data}
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise APIConnectionError(f"Streaming connection failed to {url}: {str(exc)}") from exc

    def stream_bytes(
        self,
        path: str,
        json_body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Generator[bytes, None, None]:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        try:
            with self._client.stream("POST", url, json=json_body, params=params) as resp:
                _handle_error_response(resp)
                for chunk in resp.iter_bytes():
                    if chunk:
                        yield chunk
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise APIConnectionError(f"Streaming connection failed to {url}: {str(exc)}") from exc


class AsyncTransport:
    """Asynchronous HTTP transport engine using httpx.AsyncClient."""

    def __init__(self, config: _BaseConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self.config.get_headers(),
            timeout=self.config.timeout,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        json: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        retries = 0
        while True:
            try:
                resp = await self._client.request(method, url, json=json, params=params, headers=headers)
                if (resp.status_code == 429 or resp.status_code == 503) and retries < self.config.max_retries:
                    retries += 1
                    retry_after_hdr = resp.headers.get("Retry-After")
                    try:
                        delay = float(retry_after_hdr) if retry_after_hdr else 0.5 * (2 ** (retries - 1))
                    except ValueError:
                        delay = 0.5 * (2 ** (retries - 1))
                    await asyncio.sleep(delay)
                    continue

                _handle_error_response(resp)
                if resp.status_code == 204:
                    return None
                content_type = resp.headers.get("content-type", "")
                if "application/json" in content_type:
                    return resp.json()
                return resp.content
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                if retries < self.config.max_retries:
                    retries += 1
                    await asyncio.sleep(0.5 * (2 ** (retries - 1)))
                    continue
                raise APIConnectionError(f"Connection failed to {url}: {str(exc)}") from exc

    async def post_multipart(
        self,
        path: str,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        try:
            resp = await self._client.post(url, files=files, data=data, params=params)
            _handle_error_response(resp)
            if resp.status_code == 204:
                return None
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                return resp.json()
            return resp.content
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise APIConnectionError(f"Connection failed to {url}: {str(exc)}") from exc

    async def stream_sse(
        self,
        path: str,
        json_body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        headers = {"Accept": "text/event-stream"}
        try:
            async with self._client.stream("POST", url, json=json_body, params=params, headers=headers) as resp:
                _handle_error_response(resp)
                current_event = "message"
                data_lines = []
                async for line in resp.aiter_lines():
                    trimmed = line.strip()
                    if not trimmed:
                        if data_lines:
                            data_str = "\n".join(data_lines)
                            try:
                                parsed_data = json.loads(data_str)
                            except Exception:
                                parsed_data = data_str
                            yield {"event": current_event, "data": parsed_data}
                            current_event = "message"
                            data_lines = []
                        continue
                    if trimmed.startswith(":"):
                        continue
                    if trimmed.startswith("event:"):
                        current_event = trimmed[6:].strip()
                    elif trimmed.startswith("data:"):
                        data_lines.append(trimmed[5:].strip())
                if data_lines:
                    data_str = "\n".join(data_lines)
                    try:
                        parsed_data = json.loads(data_str)
                    except Exception:
                        parsed_data = data_str
                    yield {"event": current_event, "data": parsed_data}
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise APIConnectionError(f"Streaming connection failed to {url}: {str(exc)}") from exc

    async def stream_bytes(
        self,
        path: str,
        json_body: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[bytes, None]:
        url = path if path.startswith("http") else f"{self.config.base_url}{path}"
        try:
            async with self._client.stream("POST", url, json=json_body, params=params) as resp:
                _handle_error_response(resp)
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise APIConnectionError(f"Streaming connection failed to {url}: {str(exc)}") from exc
