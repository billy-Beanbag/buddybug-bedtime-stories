from __future__ import annotations

from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_HEADER = "X-Request-ID"
_request_id_context: ContextVar[str | None] = ContextVar("buddybug_request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_context.get()


def set_request_id(request_id: str) -> None:
    _request_id_context.set(request_id)


def clear_request_id() -> None:
    _request_id_context.set(None)


def get_request_id_from_request(request: Request | None) -> str | None:
    if request is None:
        return get_request_id()
    return getattr(request.state, "request_id", None) or get_request_id()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to request state, response headers, and logging context."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        request.state.request_id = request_id
        token = _request_id_context.set(request_id)
        try:
            response = await call_next(request)
        finally:
            _request_id_context.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
