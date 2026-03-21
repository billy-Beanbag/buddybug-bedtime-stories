from __future__ import annotations

import json
from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    ChildProfile,
    DataRequest,
    LegalAcceptance,
    PrivacyPreference,
    ReadingProgress,
    SupportTicket,
    User,
    UserLibraryItem,
    UserStoryFeedback,
)
from app.schemas.billing_schema import BillingStatusResponse
from app.schemas.privacy_schema import DataRequestUpdate, PrivacyPreferenceUpdate
from app.services.billing_service import build_billing_status_response
from app.services.child_profile_service import validate_child_profile_ownership
from app.services.review_service import utc_now
from app.services.storage_service import get_asset_url, save_bytes

LEGAL_DOCUMENT_TYPES = {"terms_of_service", "privacy_policy"}
LEGAL_ACCEPTANCE_SOURCES = {"register", "profile_update", "admin", "migration"}
DATA_REQUEST_TYPES = {
    "export_account_data",
    "export_child_data",
    "delete_account_data",
    "delete_child_data",
}
DATA_REQUEST_STATUSES = {"pending", "in_progress", "completed", "rejected", "canceled"}
ACTIVE_DATA_REQUEST_STATUSES = {"pending", "in_progress"}


def record_legal_acceptance(
    session: Session,
    *,
    user_id: int,
    document_type: str,
    document_version: str,
    source: str,
) -> LegalAcceptance:
    if document_type not in LEGAL_DOCUMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported legal document type")
    if source not in LEGAL_ACCEPTANCE_SOURCES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported legal acceptance source")
    acceptance = LegalAcceptance(
        user_id=user_id,
        document_type=document_type,
        document_version=document_version,
        source=source,
    )
    session.add(acceptance)
    session.commit()
    session.refresh(acceptance)
    return acceptance


def list_legal_acceptances_for_user(session: Session, *, user_id: int) -> list[LegalAcceptance]:
    statement = (
        select(LegalAcceptance)
        .where(LegalAcceptance.user_id == user_id)
        .order_by(LegalAcceptance.accepted_at.desc(), LegalAcceptance.id.desc())
    )
    return list(session.exec(statement).all())


def get_latest_legal_acceptance(session: Session, *, user_id: int, document_type: str) -> LegalAcceptance | None:
    statement = (
        select(LegalAcceptance)
        .where(LegalAcceptance.user_id == user_id, LegalAcceptance.document_type == document_type)
        .order_by(LegalAcceptance.accepted_at.desc(), LegalAcceptance.id.desc())
    )
    return session.exec(statement).first()


def get_privacy_preference(session: Session, *, user_id: int) -> PrivacyPreference | None:
    statement = select(PrivacyPreference).where(PrivacyPreference.user_id == user_id)
    return session.exec(statement).first()


def get_or_create_privacy_preference(session: Session, *, user_id: int) -> PrivacyPreference:
    preference = get_privacy_preference(session, user_id=user_id)
    if preference is not None:
        return preference
    preference = PrivacyPreference(user_id=user_id)
    session.add(preference)
    session.commit()
    session.refresh(preference)
    return preference


def update_privacy_preference(
    session: Session,
    *,
    user_id: int,
    payload: PrivacyPreferenceUpdate,
) -> PrivacyPreference:
    preference = get_or_create_privacy_preference(session, user_id=user_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(preference, field_name, value)
    preference.updated_at = utc_now()
    session.add(preference)
    session.commit()
    session.refresh(preference)
    return preference


def recommendation_personalization_allowed(session: Session, *, user_id: int) -> bool:
    return get_or_create_privacy_preference(session, user_id=user_id).allow_recommendation_personalization


def create_data_request(
    session: Session,
    *,
    user: User,
    request_type: str,
    child_profile_id: int | None = None,
    reason: str | None = None,
) -> DataRequest:
    _validate_data_request_type(request_type)
    child_profile = validate_child_profile_ownership(session, user_id=user.id, child_profile_id=child_profile_id)
    if request_type.endswith("_child_data") and child_profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="child_profile_id is required for child data requests")
    if request_type.endswith("_account_data") and child_profile_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="child_profile_id is only allowed for child data requests")
    data_request = DataRequest(
        user_id=user.id,
        child_profile_id=child_profile.id if child_profile is not None else None,
        request_type=request_type,
        status="pending",
        reason=reason,
    )
    session.add(data_request)
    session.commit()
    session.refresh(data_request)
    return data_request


def list_data_requests_for_user(session: Session, *, user_id: int) -> list[DataRequest]:
    statement = (
        select(DataRequest)
        .where(DataRequest.user_id == user_id)
        .order_by(DataRequest.requested_at.desc(), DataRequest.id.desc())
    )
    return list(session.exec(statement).all())


def list_active_data_requests_for_user(session: Session, *, user_id: int) -> list[DataRequest]:
    statement = (
        select(DataRequest)
        .where(DataRequest.user_id == user_id, DataRequest.status.in_(ACTIVE_DATA_REQUEST_STATUSES))
        .order_by(DataRequest.requested_at.desc(), DataRequest.id.desc())
    )
    return list(session.exec(statement).all())


def list_data_requests_for_admin(
    session: Session,
    *,
    status_value: str | None = None,
    request_type: str | None = None,
    limit: int = 100,
) -> list[DataRequest]:
    statement = select(DataRequest).order_by(DataRequest.requested_at.desc(), DataRequest.id.desc()).limit(limit)
    if status_value is not None:
        if status_value not in DATA_REQUEST_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported data request status")
        statement = statement.where(DataRequest.status == status_value)
    if request_type is not None:
        _validate_data_request_type(request_type)
        statement = statement.where(DataRequest.request_type == request_type)
    return list(session.exec(statement).all())


def validate_data_request_access(session: Session, *, user: User, request_id: int) -> DataRequest:
    data_request = session.get(DataRequest, request_id)
    if data_request is None or data_request.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data request not found")
    return data_request


def build_account_export_payload(session: Session, *, user: User) -> dict[str, object]:
    child_profiles = list(
        session.exec(select(ChildProfile).where(ChildProfile.user_id == user.id).order_by(ChildProfile.created_at.asc())).all()
    )
    return {
        "export_type": "account",
        "generated_at": utc_now().isoformat(),
        "user": _serialize_user(user),
        "child_profiles": [_serialize_model(child_profile) for child_profile in child_profiles],
        "library_items": [_serialize_model(item) for item in _list_library_items(session, user_id=user.id)],
        "reading_progress": [_serialize_model(item) for item in _list_reading_progress_for_account(session, user=user)],
        "feedback": [_serialize_model(item) for item in _list_feedback_for_account(session, user_id=user.id)],
        "privacy_preference": _serialize_optional(get_privacy_preference(session, user_id=user.id)),
        "billing_summary": _serialize_billing_summary(build_billing_status_response(user)),
        "support_tickets": [_serialize_model(ticket) for ticket in _list_support_tickets(session, user_id=user.id)],
        "data_requests": [_serialize_model(item) for item in list_data_requests_for_user(session, user_id=user.id)],
        "legal_acceptances": [_serialize_model(item) for item in list_legal_acceptances_for_user(session, user_id=user.id)],
        "retention_readiness": build_retention_readiness_summary(session, user=user),
    }


def build_child_export_payload(session: Session, *, user: User, child_profile_id: int) -> dict[str, object]:
    child_profile = validate_child_profile_ownership(session, user_id=user.id, child_profile_id=child_profile_id)
    return {
        "export_type": "child",
        "generated_at": utc_now().isoformat(),
        "user": _serialize_user(user),
        "child_profile": _serialize_model(child_profile),
        "library_items": [
            _serialize_model(item)
            for item in _list_library_items(session, user_id=user.id, child_profile_id=child_profile.id)
        ],
        "reading_progress": [
            _serialize_model(item)
            for item in _list_reading_progress_for_child(session, user=user, child_profile_id=child_profile.id)
        ],
        "feedback": [
            _serialize_model(item)
            for item in _list_feedback_for_account(session, user_id=user.id, child_profile_id=child_profile.id)
        ],
        "support_tickets": [
            _serialize_model(ticket)
            for ticket in _list_support_tickets(session, user_id=user.id, child_profile_id=child_profile.id)
        ],
        "data_requests": [
            _serialize_model(item)
            for item in list_data_requests_for_user(session, user_id=user.id)
            if item.child_profile_id == child_profile.id
        ],
        "retention_readiness": build_retention_readiness_summary(session, user=user, child_profile=child_profile),
    }


def complete_data_request(
    session: Session,
    *,
    data_request: DataRequest,
    output_url: str | None = None,
    notes: str | None = None,
) -> DataRequest:
    data_request.status = "completed"
    data_request.output_url = output_url
    data_request.notes = notes if notes is not None else data_request.notes
    data_request.completed_at = utc_now()
    data_request.updated_at = utc_now()
    session.add(data_request)
    session.commit()
    session.refresh(data_request)
    return data_request


def update_data_request(
    session: Session,
    *,
    data_request: DataRequest,
    payload: DataRequestUpdate,
) -> DataRequest:
    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data:
        status_value = update_data["status"]
        if status_value is not None and status_value not in DATA_REQUEST_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported data request status")
    for field_name, value in update_data.items():
        setattr(data_request, field_name, value)
    data_request.updated_at = utc_now()
    session.add(data_request)
    session.commit()
    session.refresh(data_request)
    return data_request


def process_export_data_request(session: Session, *, data_request: DataRequest) -> DataRequest:
    if data_request.request_type not in {"export_account_data", "export_child_data"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only export requests can be processed")

    user = session.get(User, data_request.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request owner not found")

    payload = (
        build_child_export_payload(session, user=user, child_profile_id=data_request.child_profile_id)
        if data_request.request_type == "export_child_data"
        else build_account_export_payload(session, user=user)
    )
    asset_path = _build_export_asset_path(data_request=data_request)
    saved_path = save_bytes(asset_path, json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8"))
    return complete_data_request(
        session,
        data_request=data_request,
        output_url=get_asset_url(saved_path),
        notes="JSON export prepared",
    )


def build_retention_readiness_summary(
    session: Session,
    *,
    user: User,
    child_profile: ChildProfile | None = None,
) -> dict[str, object]:
    if child_profile is not None:
        progress_rows = _list_reading_progress_for_child(session, user=user, child_profile_id=child_profile.id)
        feedback_rows = _list_feedback_for_account(session, user_id=user.id, child_profile_id=child_profile.id)
        support_rows = _list_support_tickets(session, user_id=user.id, child_profile_id=child_profile.id)
    else:
        progress_rows = _list_reading_progress_for_account(session, user=user)
        feedback_rows = _list_feedback_for_account(session, user_id=user.id)
        support_rows = _list_support_tickets(session, user_id=user.id)

    return {
        "analytics_personalization_opt_in": get_or_create_privacy_preference(session, user_id=user.id).analytics_personalization_opt_in,
        "reading_progress_count": len(progress_rows),
        "feedback_count": len(feedback_rows),
        "support_ticket_count": len(support_rows),
        "latest_reading_activity_at": _latest_timestamp(progress_rows, "updated_at"),
        "latest_feedback_at": _latest_timestamp(feedback_rows, "updated_at"),
        "latest_support_activity_at": _latest_timestamp(support_rows, "updated_at"),
    }


def _validate_data_request_type(request_type: str) -> str:
    if request_type not in DATA_REQUEST_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported data request type")
    return request_type


def _list_library_items(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None = None,
) -> list[UserLibraryItem]:
    statement = select(UserLibraryItem).where(UserLibraryItem.user_id == user_id).order_by(UserLibraryItem.created_at.asc())
    if child_profile_id is not None:
        statement = statement.where(UserLibraryItem.child_profile_id == child_profile_id)
    return list(session.exec(statement).all())


def _list_feedback_for_account(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None = None,
) -> list[UserStoryFeedback]:
    statement = select(UserStoryFeedback).where(UserStoryFeedback.user_id == user_id).order_by(UserStoryFeedback.created_at.asc())
    if child_profile_id is not None:
        statement = statement.where(UserStoryFeedback.child_profile_id == child_profile_id)
    return list(session.exec(statement).all())


def _list_reading_progress_for_account(session: Session, *, user: User) -> list[ReadingProgress]:
    return list(
        session.exec(
            select(ReadingProgress)
            .where(ReadingProgress.reader_identifier == f"user:{user.id}")
            .order_by(ReadingProgress.created_at.asc())
        ).all()
    )


def _list_reading_progress_for_child(
    session: Session,
    *,
    user: User,
    child_profile_id: int,
) -> list[ReadingProgress]:
    return list(
        session.exec(
            select(ReadingProgress)
            .where(
                ReadingProgress.reader_identifier == f"user:{user.id}",
                ReadingProgress.child_profile_id == child_profile_id,
            )
            .order_by(ReadingProgress.created_at.asc())
        ).all()
    )


def _list_support_tickets(
    session: Session,
    *,
    user_id: int,
    child_profile_id: int | None = None,
) -> list[SupportTicket]:
    statement = select(SupportTicket).where(SupportTicket.user_id == user_id).order_by(SupportTicket.created_at.asc())
    if child_profile_id is not None:
        statement = statement.where(SupportTicket.child_profile_id == child_profile_id)
    return list(session.exec(statement).all())


def _build_export_asset_path(*, data_request: DataRequest) -> str:
    suffix = f"child-{data_request.child_profile_id}" if data_request.child_profile_id is not None else "account"
    return f"mock-assets/privacy-exports/user-{data_request.user_id}/request-{data_request.id}-{suffix}.json"


def _serialize_model(model: object) -> dict[str, object]:
    if hasattr(model, "model_dump"):
        return getattr(model, "model_dump")(mode="json")
    raise TypeError("Unsupported model serialization")


def _serialize_optional(model: object | None) -> dict[str, object] | None:
    return None if model is None else _serialize_model(model)


def _serialize_billing_summary(summary: BillingStatusResponse) -> dict[str, object]:
    return {
        "user_id": summary.user_id,
        "subscription_tier": summary.subscription_tier,
        "subscription_status": summary.subscription_status,
        "subscription_expires_at": summary.subscription_expires_at.isoformat() if summary.subscription_expires_at else None,
        "trial_ends_at": summary.trial_ends_at.isoformat() if summary.trial_ends_at else None,
        "has_premium_access": summary.has_premium_access,
    }


def _serialize_user(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "country": user.country,
        "language": user.language,
        "is_active": user.is_active,
        "subscription_tier": user.subscription_tier,
        "subscription_status": user.subscription_status,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


def _latest_timestamp(rows: Sequence[object], field_name: str) -> str | None:
    timestamps = [getattr(row, field_name, None) for row in rows if getattr(row, field_name, None) is not None]
    if not timestamps:
        return None
    return max(timestamps).isoformat()
