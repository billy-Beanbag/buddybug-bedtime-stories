from fastapi import APIRouter, Depends, Header
from sqlmodel import Session

from app.database import get_session
from app.models import User
from app.services.message_experiment_service import get_message_experiment_bundle
from app.utils.dependencies import get_optional_current_user

router = APIRouter(prefix="/message-experiments", tags=["message-experiments"])


@router.get("/bundle", summary="Get frontend message experiment copy bundle")
def get_message_bundle(
    x_reader_identifier: str | None = Header(default=None, alias="X-Reader-Identifier"),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> dict[str, dict[str, object]]:
    return get_message_experiment_bundle(
        session,
        user=current_user,
        reader_identifier=x_reader_identifier,
    )
