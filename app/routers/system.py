"""System routes: health, login-check, ready. Registered first so they always work."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlmodel import Session, select

from app.config import APP_NAME, DEBUG
from app.database import get_session
from app.models import User
from app.services.admin_service import delete_workflow_record
from app.utils.auth import verify_password
from app.utils.dev_seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD
from app.utils.dependencies import get_current_admin_user
from app.middleware.request_context import get_request_id_from_request

router = APIRouter(tags=["system"])


@router.post(
    "/delete-workflow-record",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a workflow record (book, draft, idea) and all dependencies",
)
def delete_workflow_record_route(
    book_id: int | None = Query(default=None),
    draft_id: int | None = Query(default=None),
    idea_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> Response:
    if not any([book_id is not None, draft_id is not None, idea_id is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of book_id, draft_id, or idea_id is required",
        )
    delete_workflow_record(session, book_id=book_id, draft_id=draft_id, idea_id=idea_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/health")
def health(
    login_check: bool = Query(default=False, alias="login_check"),
    session: Session = Depends(get_session),
):
    """Health endpoint. Add ?login-check=1 to diagnose admin login."""
    out = {"status": "ok", "app": APP_NAME}
    if login_check and str(login_check).lower() in ("1", "true", "yes"):
        user = session.exec(select(User).where(User.email == DEMO_ADMIN_EMAIL.lower())).first()
        if not user:
            out["admin_exists"] = False
            out["hint"] = "Run: python scripts/fix_dev_setup.py then restart backend"
        else:
            pw_ok = verify_password(DEMO_ADMIN_PASSWORD, user.password_hash)
            out["admin_exists"] = True
            out["password_ok"] = pw_ok
            out["email"] = DEMO_ADMIN_EMAIL
            out["hint"] = "Login should work" if pw_ok else "Password wrong - restart backend to fix"
    return out


@router.get("/login-check")
def login_check(session: Session = Depends(get_session)) -> JSONResponse:
    """Verify admin login works. Visit http://127.0.0.1:8000/login-check to diagnose."""
    user = session.exec(select(User).where(User.email == DEMO_ADMIN_EMAIL.lower())).first()
    if not user:
        return JSONResponse(
            status_code=200,
            content={
                "admin_exists": False,
                "hint": "Run: python scripts/fix_dev_setup.py then restart backend",
            },
        )
    pw_ok = verify_password(DEMO_ADMIN_PASSWORD, user.password_hash)
    return JSONResponse(
        status_code=200,
        content={
            "admin_exists": True,
            "password_ok": pw_ok,
            "email": DEMO_ADMIN_EMAIL,
            "hint": "Login should work" if pw_ok else "Password wrong - restart backend to fix",
        },
    )


@router.get("/ready")
def ready(session: Session = Depends(get_session)) -> JSONResponse:
    """Readiness check with DB connectivity."""
    try:
        session.exec(text("SELECT 1"))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Readiness check failed", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "app": APP_NAME,
                "request_id": get_request_id_from_request(None),
                "detail": "Database is unavailable" if not DEBUG else str(exc),
            },
        )
    return JSONResponse(status_code=200, content={"status": "ready", "app": APP_NAME})
