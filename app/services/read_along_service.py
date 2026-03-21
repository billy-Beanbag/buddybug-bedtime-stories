from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import choice

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import ReadAlongParticipant, ReadAlongSession, User
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.reader_service import get_published_book_or_404
from app.services.review_service import utc_now

READ_ALONG_SESSION_STATUSES = {"active", "ended", "expired"}
READ_ALONG_PLAYBACK_STATES = {"paused", "reading", "finished"}
READ_ALONG_PARTICIPANT_ROLES = {"owner", "participant"}
JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DEFAULT_SESSION_TTL_HOURS = 24


def _validate_status(status_value: str) -> str:
    if status_value not in READ_ALONG_SESSION_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported read-along session status")
    return status_value


def _validate_playback_state(playback_state: str) -> str:
    if playback_state not in READ_ALONG_PLAYBACK_STATES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported playback state")
    return playback_state


def _validate_page_number(current_page_number: int) -> int:
    if current_page_number < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="current_page_number must be non-negative")
    return current_page_number


def generate_join_code(session: Session, *, length: int = 6) -> str:
    for _ in range(10):
        join_code = "".join(choice(JOIN_CODE_ALPHABET) for _ in range(length))
        existing = session.exec(select(ReadAlongSession).where(ReadAlongSession.join_code == join_code)).first()
        if existing is None:
            return join_code
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate join code")


def _get_session_or_404(session: Session, session_id: int) -> ReadAlongSession:
    read_along_session = session.get(ReadAlongSession, session_id)
    if read_along_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Read-along session not found")
    return read_along_session


def _get_participant(
    session: Session,
    *,
    session_id: int,
    user_id: int,
    child_profile_id: int | None,
) -> ReadAlongParticipant | None:
    statement = select(ReadAlongParticipant).where(
        ReadAlongParticipant.session_id == session_id,
        ReadAlongParticipant.user_id == user_id,
    )
    if child_profile_id is None:
        statement = statement.where(ReadAlongParticipant.child_profile_id == None)  # noqa: E711
    else:
        statement = statement.where(ReadAlongParticipant.child_profile_id == child_profile_id)
    return session.exec(statement).first()


def _normalize_datetime_for_compare(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _mark_expired_if_needed(session: Session, read_along_session: ReadAlongSession) -> ReadAlongSession:
    if (
        read_along_session.status == "active"
        and read_along_session.expires_at is not None
        and _normalize_datetime_for_compare(read_along_session.expires_at) <= utc_now()
    ):
        read_along_session.status = "expired"
        read_along_session.ended_at = read_along_session.ended_at or utc_now()
        read_along_session.updated_at = utc_now()
        session.add(read_along_session)
        session.commit()
        session.refresh(read_along_session)
    return read_along_session


def validate_read_along_access(
    session: Session,
    *,
    read_along_session: ReadAlongSession,
    current_user: User,
) -> ReadAlongSession:
    read_along_session = _mark_expired_if_needed(session, read_along_session)
    if read_along_session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this read-along session")
    return read_along_session


def create_read_along_session(
    session: Session,
    *,
    current_user: User,
    book_id: int,
    child_profile_id: int | None,
    language: str | None,
    current_page_number: int,
    playback_state: str,
) -> tuple[ReadAlongSession, list[ReadAlongParticipant]]:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    get_published_book_or_404(session, book_id)
    _validate_page_number(current_page_number)
    _validate_playback_state(playback_state)

    now = utc_now()
    read_along_session = ReadAlongSession(
        user_id=current_user.id,
        child_profile_id=child_profile_id,
        book_id=book_id,
        join_code=generate_join_code(session),
        status="active",
        current_page_number=current_page_number,
        playback_state=playback_state,
        language=language.lower() if language else None,
        expires_at=now + timedelta(hours=DEFAULT_SESSION_TTL_HOURS),
    )
    session.add(read_along_session)
    session.commit()
    session.refresh(read_along_session)

    participant = ReadAlongParticipant(
        session_id=read_along_session.id,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
        role="owner",
        joined_at=now,
        last_seen_at=now,
    )
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return read_along_session, [participant]


def get_session_by_join_code(session: Session, *, join_code: str) -> ReadAlongSession:
    normalized_code = join_code.strip().upper()
    if not normalized_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="join_code is required")
    read_along_session = session.exec(
        select(ReadAlongSession).where(ReadAlongSession.join_code == normalized_code)
    ).first()
    if read_along_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Read-along session not found")
    return _mark_expired_if_needed(session, read_along_session)


def join_read_along_session(
    session: Session,
    *,
    current_user: User,
    join_code: str,
    child_profile_id: int | None,
) -> tuple[ReadAlongSession, ReadAlongParticipant]:
    validate_child_profile_ownership(session, user_id=current_user.id, child_profile_id=child_profile_id)
    read_along_session = get_session_by_join_code(session, join_code=join_code)
    validate_read_along_access(session, read_along_session=read_along_session, current_user=current_user)
    if read_along_session.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active read-along sessions can be joined")

    participant = _get_participant(
        session,
        session_id=read_along_session.id,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
    )
    if participant is None:
        participant = ReadAlongParticipant(
            session_id=read_along_session.id,
            user_id=current_user.id,
            child_profile_id=child_profile_id,
            role="participant",
            joined_at=utc_now(),
            last_seen_at=utc_now(),
        )
    else:
        participant.last_seen_at = utc_now()
        participant.updated_at = utc_now()

    session.add(participant)
    session.commit()
    session.refresh(participant)
    return read_along_session, participant


def list_read_along_sessions_for_user(
    session: Session,
    *,
    current_user: User,
    status_filter: str | None,
    limit: int,
) -> list[ReadAlongSession]:
    if status_filter is not None:
        _validate_status(status_filter)
    statement = (
        select(ReadAlongSession)
        .where(ReadAlongSession.user_id == current_user.id)
        .order_by(ReadAlongSession.updated_at.desc())
        .limit(limit)
    )
    if status_filter is not None:
        statement = statement.where(ReadAlongSession.status == status_filter)
    sessions = list(session.exec(statement).all())
    return [_mark_expired_if_needed(session, item) for item in sessions]


def list_session_participants(session: Session, *, session_id: int) -> list[ReadAlongParticipant]:
    statement = (
        select(ReadAlongParticipant)
        .where(ReadAlongParticipant.session_id == session_id)
        .order_by(ReadAlongParticipant.joined_at.asc(), ReadAlongParticipant.id.asc())
    )
    return list(session.exec(statement).all())


def touch_participant_seen(
    session: Session,
    *,
    read_along_session: ReadAlongSession,
    current_user: User,
    child_profile_id: int | None,
) -> ReadAlongParticipant | None:
    participant = _get_participant(
        session,
        session_id=read_along_session.id,
        user_id=current_user.id,
        child_profile_id=child_profile_id,
    )
    if participant is None:
        return None
    participant.last_seen_at = utc_now()
    participant.updated_at = utc_now()
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return participant


def get_read_along_detail(
    session: Session,
    *,
    session_id: int,
    current_user: User,
) -> tuple[ReadAlongSession, list[ReadAlongParticipant]]:
    read_along_session = _get_session_or_404(session, session_id)
    read_along_session = validate_read_along_access(session, read_along_session=read_along_session, current_user=current_user)
    participants = list_session_participants(session, session_id=read_along_session.id)
    return read_along_session, participants


def update_read_along_session(
    session: Session,
    *,
    session_id: int,
    current_user: User,
    current_page_number: int | None = None,
    playback_state: str | None = None,
    status_value: str | None = None,
    ended_at=None,
) -> ReadAlongSession:
    read_along_session = _get_session_or_404(session, session_id)
    read_along_session = validate_read_along_access(session, read_along_session=read_along_session, current_user=current_user)

    if current_page_number is not None:
        read_along_session.current_page_number = _validate_page_number(current_page_number)
    if playback_state is not None:
        read_along_session.playback_state = _validate_playback_state(playback_state)
    if status_value is not None:
        read_along_session.status = _validate_status(status_value)
        if status_value in {"ended", "expired"}:
            read_along_session.ended_at = ended_at or utc_now()
    if ended_at is not None:
        read_along_session.ended_at = ended_at

    read_along_session.updated_at = utc_now()
    session.add(read_along_session)
    session.commit()
    session.refresh(read_along_session)
    return read_along_session


def end_read_along_session(
    session: Session,
    *,
    session_id: int,
    current_user: User,
) -> ReadAlongSession:
    return update_read_along_session(
        session,
        session_id=session_id,
        current_user=current_user,
        status_value="ended",
        playback_state="finished",
        ended_at=utc_now(),
    )
