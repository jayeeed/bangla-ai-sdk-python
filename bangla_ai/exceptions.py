from typing import Any, Dict, Optional


class BanglaAIError(Exception):
    """Base exception for all errors raised by the Bangla AI SDK."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class APIConnectionError(BanglaAIError):
    """Raised when communication with the Bangla AI Gateway fails (network or DNS timeout)."""

    def __init__(self, message: str = "Failed to connect to the Bangla AI Gateway.") -> None:
        super().__init__(message)


class APIStatusError(BanglaAIError):
    """Raised when the gateway responds with an HTTP error status code."""

    def __init__(
        self,
        message: str,
        status_code: int,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code or "UNKNOWN_ERROR"
        self.request_id = request_id
        self.response_body = response_body or {}

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(status_code={self.status_code}, "
            f"code={self.code!r}, message={self.message!r}, request_id={self.request_id!r})"
        )


class BadRequestError(APIStatusError):
    """HTTP 400: Malformed request or validation failure."""
    pass


class AuthenticationError(APIStatusError):
    """HTTP 401: Invalid, expired, or missing API key or Bearer token."""
    pass


class PermissionDeniedError(APIStatusError):
    """HTTP 403: Caller lacks required permission or modality scope."""
    pass


class NotFoundError(APIStatusError):
    """HTTP 404: The requested resource (chat, turn, attachment, job) does not exist."""
    pass


class RateLimitError(APIStatusError):
    """HTTP 429: Request quota exceeded."""

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        code: Optional[str] = "RATE_LIMIT_EXCEEDED",
        request_id: Optional[str] = None,
        retry_after: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            code=code,
            request_id=request_id,
            response_body=response_body,
        )
        self.retry_after = retry_after


class InternalServerError(APIStatusError):
    """HTTP 500: Unexpected internal gateway failure."""
    pass


class UpstreamServiceError(APIStatusError):
    """HTTP 502: The private GPU inference microservice (LLM, OCR, ASR, TTS, STS) returned an error or is unreachable."""
    pass


class ServiceUnavailableError(APIStatusError):
    """HTTP 503: The service is temporarily saturated or under backpressure."""

    def __init__(
        self,
        message: str,
        status_code: int = 503,
        code: Optional[str] = "SERVICE_UNAVAILABLE",
        request_id: Optional[str] = None,
        retry_after: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            code=code,
            request_id=request_id,
            response_body=response_body,
        )
        self.retry_after = retry_after
