from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, AUTH_RATE_LIMIT_PER_MINUTE, PRIVACY_POLICY_VERSION, TERMS_VERSION
from app.database import get_session
from app.middleware.rate_limit import create_rate_limit_dependency
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.user_schema import TokenResponse, UserCreate, UserLogin, UserRead, UserUpdate
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.growth_service import attribute_user_to_referral, get_referral_code_by_value
from app.services.privacy_service import record_legal_acceptance
from app.services.user_service import (
    authenticate_user,
    deactivate_user,
    get_user_by_id,
    register_user,
    update_user,
)
from app.utils.auth import create_access_token
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])
auth_rate_limit = create_rate_limit_dependency(limit=AUTH_RATE_LIMIT_PER_MINUTE, scope_key="auth")


def _build_token_response(user: User) -> TokenResponse:
    access_token = create_access_token(
        {
            "sub": user.email,
            "user_id": user.id,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=access_token, user=user)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    dependencies=[Depends(auth_rate_limit)],
)
def register(
    payload: UserCreate,
    request: Request,
    session: Session = Depends(get_session),
) -> TokenResponse:
    validated_referral_code = None
    if payload.referral_code:
        validated_referral_code = get_referral_code_by_value(session, code=payload.referral_code).code
    user = register_user(
        session,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        country=payload.country,
        language=payload.language,
    )
    if validated_referral_code:
        attribution = attribute_user_to_referral(
            session,
            referred_user=user,
            referral_code_value=validated_referral_code,
        )
        create_audit_log(
            session,
            action_type="referral_attribution_created",
            entity_type="referral_attribution",
            entity_id=str(attribution.id),
            summary=f"Attributed signup for user {user.email}",
            actor_user=user,
            request_id=get_request_id_from_request(request),
            metadata={"referral_code": validated_referral_code, "referrer_user_id": attribution.referrer_user_id},
        )
        track_event_safe(
            session,
            event_name="referral_signup_attributed",
            user=user,
            metadata={"referrer_user_id": attribution.referrer_user_id, "referral_code": validated_referral_code},
        )
    if payload.accept_terms:
        acceptance = record_legal_acceptance(
            session,
            user_id=user.id,
            document_type="terms_of_service",
            document_version=TERMS_VERSION,
            source="register",
        )
        create_audit_log(
            session,
            action_type="legal_acceptance_recorded",
            entity_type="legal_acceptance",
            entity_id=str(acceptance.id),
            summary=f"Recorded terms acceptance for user {user.id}",
            actor_user=user,
            request_id=get_request_id_from_request(request),
            metadata={"document_type": acceptance.document_type, "document_version": acceptance.document_version},
        )
    if payload.accept_privacy:
        acceptance = record_legal_acceptance(
            session,
            user_id=user.id,
            document_type="privacy_policy",
            document_version=PRIVACY_POLICY_VERSION,
            source="register",
        )
        create_audit_log(
            session,
            action_type="legal_acceptance_recorded",
            entity_type="legal_acceptance",
            entity_id=str(acceptance.id),
            summary=f"Recorded privacy acceptance for user {user.id}",
            actor_user=user,
            request_id=get_request_id_from_request(request),
            metadata={"document_type": acceptance.document_type, "document_version": acceptance.document_version},
        )
    return _build_token_response(user)


@router.get("/login-check", summary="Diagnose admin login (admin exists, password ok)")
def login_check(session: Session = Depends(get_session)) -> JSONResponse:
    """Verify admin login. Visit http://127.0.0.1:8000/users/login-check"""
    user = session.exec(select(User).where(User.email == DEMO_ADMIN_EMAIL.lower())).first()
    if not user:
        return JSONResponse(
            status_code=200,
            content={"admin_exists": False, "hint": "Run: python scripts/fix_dev_setup.py then restart backend"},
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


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
    dependencies=[Depends(auth_rate_limit)],
)
def login(payload: UserLogin, session: Session = Depends(get_session)) -> TokenResponse:
    user = authenticate_user(session, email=payload.email, password=payload.password)
    return _build_token_response(user)


@router.get("/me", response_model=UserRead, summary="Get the currently authenticated user")
def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserRead, summary="Update the current user's profile")
def update_me(
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> User:
    return update_user(
        session,
        user=current_user,
        display_name=payload.display_name,
        country=payload.country,
        language=payload.language,
    )


@router.post("/me/deactivate", response_model=UserRead, summary="Deactivate the current user account")
def deactivate_me(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> User:
    return deactivate_user(session, user=current_user)


@router.get("", response_model=list[UserRead], summary="List users")
def list_users(
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> list[User]:
    statement = select(User).order_by(User.created_at.desc()).limit(limit)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    return list(session.exec(statement).all())


@router.get("/{user_id}", response_model=UserRead, summary="Get one user by id")
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_active_user),
) -> User:
    user = get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
