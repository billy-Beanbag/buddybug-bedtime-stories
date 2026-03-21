from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.database import get_session
from app.models import ApiKey, User
from app.services.api_key_service import require_scope, validate_api_key
from app.services.organization_service import get_active_membership_for_user
from app.services.user_service import get_user_by_id
from app.utils.auth import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def _get_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
    session: Session,
) -> User | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = get_user_by_id(session, parsed_user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
 ) -> User:
    user = _get_user_from_credentials(credentials, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User | None:
    return _get_user_from_credentials(credentials, session)


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def get_current_editor_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin and not current_user.is_editor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Editor access required")
    return current_user


def get_current_educator_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_admin and not current_user.is_educator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Educator access required")
    return current_user


def get_current_org_user(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
) -> User:
    if current_user.is_admin:
        return current_user
    membership = get_active_membership_for_user(session, user_id=current_user.id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization membership required")
    return current_user


def get_current_org_admin_user(
    current_user: User = Depends(get_current_org_user),
    session: Session = Depends(get_session),
) -> User:
    if current_user.is_admin:
        return current_user
    membership = get_active_membership_for_user(session, user_id=current_user.id)
    if membership is None or membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization admin access required")
    return current_user


def get_current_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> ApiKey:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    return validate_api_key(session, raw_api_key=credentials.credentials)


def require_api_scope(required_scope: str):
    def dependency(api_key: ApiKey = Depends(get_current_api_key)) -> ApiKey:
        return require_scope(api_key, required_scope=required_scope)

    return dependency
