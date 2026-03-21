from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.models import User
from app.services.i18n_service import validate_language_code
from app.services.review_service import utc_now
from app.utils.auth import hash_password, verify_password


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(session: Session, email: str) -> User | None:
    normalized_email = _normalize_email(email)
    statement = select(User).where(func.lower(User.email) == normalized_email)
    return session.exec(statement).first()


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def register_user(
    session: Session,
    *,
    email: str,
    password: str,
    display_name: str | None,
    country: str | None,
    language: str,
) -> User:
    if get_user_by_email(session, email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=_normalize_email(email),
        password_hash=hash_password(password),
        display_name=display_name,
        country=country,
        language=validate_language_code(language),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, *, email: str, password: str) -> User:
    from app.config import DEBUG
    from app.utils.dev_seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD

    user = get_user_by_email(session, email)
    pw_ok = verify_password(password, user.password_hash) if user else False
    # Dev bypass: accept demo credentials when user exists or we're in debug mode
    if not pw_ok and _normalize_email(email) == DEMO_ADMIN_EMAIL.lower():
        if password in ("demo", DEMO_ADMIN_PASSWORD):
            if user:
                pw_ok = True
            elif DEBUG:
                # Create demo admin on-the-fly if missing (e.g. fresh Postgres in Docker)
                from app.utils.dev_seed import ensure_demo_user

                user = ensure_demo_user(
                    session,
                    email=DEMO_ADMIN_EMAIL,
                    password=DEMO_ADMIN_PASSWORD,
                    display_name="Buddybug Admin",
                    is_admin=True,
                    subscription_tier="premium",
                    subscription_status="active",
                )
                pw_ok = True
    if user is None or not pw_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


def update_user(
    session: Session,
    *,
    user: User,
    display_name: str | None = None,
    country: str | None = None,
    language: str | None = None,
    is_active: bool | None = None,
) -> User:
    if display_name is not None:
        user.display_name = display_name
    if country is not None:
        user.country = country
    if language is not None:
        user.language = validate_language_code(language)
    if is_active is not None:
        user.is_active = is_active
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def deactivate_user(session: Session, *, user: User) -> User:
    user.is_active = False
    user.updated_at = utc_now()
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
