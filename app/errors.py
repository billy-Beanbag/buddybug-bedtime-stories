from __future__ import annotations

import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.config import DEBUG
from app.middleware.request_context import get_request_id_from_request

logger = logging.getLogger(__name__)


def build_error_payload(
    *,
    detail: str,
    request: Request | None,
    error_code: str,
    extra_detail: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "detail": detail,
        "error_code": error_code,
        "request_id": get_request_id_from_request(request),
    }
    if DEBUG and extra_detail is not None:
        payload["debug_detail"] = extra_detail
    return payload


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        payload = {
            "detail": detail.get("detail", "Request failed"),
            "error_code": detail.get("error_code", f"http_{exc.status_code}"),
            "request_id": get_request_id_from_request(request),
        }
        if DEBUG and "debug_detail" in detail:
            payload["debug_detail"] = detail["debug_detail"]
    else:
        payload = build_error_payload(
            detail=str(detail),
            request=request,
            error_code=f"http_{exc.status_code}",
        )
    return JSONResponse(status_code=exc.status_code, content=payload, headers=exc.headers)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception during request",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )
    payload = build_error_payload(
        detail="Internal server error",
        request=request,
        error_code="internal_server_error",
        extra_detail=str(exc),
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
