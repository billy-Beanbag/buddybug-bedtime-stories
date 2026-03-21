from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session, func, select

from app.database import get_session
from app.models import Character
from app.schemas.character_schema import CharacterCreate, CharacterRead, CharacterUpdate

router = APIRouter(prefix="/characters", tags=["characters"])


def _normalize_name(name: str) -> str:
    return name.strip().casefold()


def _get_character_or_404(session: Session, character_id: int) -> Character:
    character = session.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return character


def _get_character_by_name(session: Session, name: str) -> Character | None:
    statement = select(Character).where(func.lower(Character.name) == _normalize_name(name))
    return session.exec(statement).first()


@router.get("", response_model=list[CharacterRead], summary="List canonical characters")
def list_characters(
    include_inactive: bool = Query(default=False),
    session: Session = Depends(get_session),
) -> list[Character]:
    statement = select(Character).order_by(Character.name)
    if not include_inactive:
        statement = statement.where(Character.is_active.is_(True))
    return list(session.exec(statement).all())


@router.get("/{character_id}", response_model=CharacterRead, summary="Get a character by id")
def get_character(character_id: int, session: Session = Depends(get_session)) -> Character:
    return _get_character_or_404(session, character_id)


@router.get(
    "/by-name/{name}",
    response_model=CharacterRead,
    summary="Get a character by exact name",
)
def get_character_by_name(name: str, session: Session = Depends(get_session)) -> Character:
    character = _get_character_by_name(session, name)
    if character is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return character


@router.post(
    "",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a canonical character",
)
def create_character(
    payload: CharacterCreate,
    session: Session = Depends(get_session),
) -> Character:
    if _get_character_by_name(session, payload.name) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Character name already exists")

    character = Character.model_validate(payload)
    session.add(character)
    session.commit()
    session.refresh(character)
    return character


@router.patch(
    "/{character_id}",
    response_model=CharacterRead,
    summary="Partially update a canonical character",
)
def update_character(
    character_id: int,
    payload: CharacterUpdate,
    session: Session = Depends(get_session),
) -> Character:
    character = _get_character_or_404(session, character_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        duplicate = _get_character_by_name(session, update_data["name"])
        if duplicate is not None and duplicate.id != character_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Character name already exists")

    for field_name, value in update_data.items():
        setattr(character, field_name, value)

    character.updated_at = datetime.now(timezone.utc)
    session.add(character)
    session.commit()
    session.refresh(character)
    return character


@router.delete(
    "/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete a canonical character",
)
def delete_character(character_id: int, session: Session = Depends(get_session)) -> Response:
    character = _get_character_or_404(session, character_id)
    character.is_active = False
    character.updated_at = datetime.now(timezone.utc)
    session.add(character)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
