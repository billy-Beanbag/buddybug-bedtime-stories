from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, desc, or_, select

from app.models import ChangelogEntry
from app.models.user import utc_now

CHANGELOG_AUDIENCES = {"internal", "user_facing"}
CHANGELOG_STATUSES = {"draft", "published", "archived"}


def _persist(session: Session, model):
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def validate_changelog_audience(audience: str) -> str:
    if audience not in CHANGELOG_AUDIENCES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid changelog audience")
    return audience


def validate_changelog_status(status_value: str) -> str:
    if status_value not in CHANGELOG_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid changelog status")
    return status_value


def _normalize_csv(value: str | None) -> str | None:
    if value is None:
        return None
    parts = [item.strip() for item in value.split(",") if item.strip()]
    return ", ".join(parts) if parts else None


def _tag_filter_conditions(column, tag_value: str):
    return or_(
        column == tag_value,
        column.like(f"{tag_value}, %"),
        column.like(f"%, {tag_value}"),
        column.like(f"%, {tag_value}, %"),
    )


def get_changelog_entry_or_404(session: Session, *, entry_id: int) -> ChangelogEntry:
    entry = session.get(ChangelogEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Changelog entry not found")
    return entry


def list_changelog_entries(
    session: Session,
    *,
    audience: str | None,
    status_value: str | None,
    area_tag: str | None,
    feature_flag_key: str | None,
    limit: int,
) -> list[ChangelogEntry]:
    statement = select(ChangelogEntry).order_by(desc(ChangelogEntry.published_at), desc(ChangelogEntry.updated_at)).limit(limit)
    if audience is not None:
        statement = statement.where(ChangelogEntry.audience == validate_changelog_audience(audience))
    if status_value is not None:
        statement = statement.where(ChangelogEntry.status == validate_changelog_status(status_value))
    if area_tag is not None and area_tag.strip():
        statement = statement.where(_tag_filter_conditions(ChangelogEntry.area_tags, area_tag.strip()))
    if feature_flag_key is not None and feature_flag_key.strip():
        statement = statement.where(_tag_filter_conditions(ChangelogEntry.feature_flag_keys, feature_flag_key.strip()))
    return list(session.exec(statement).all())


def create_changelog_entry(
    session: Session,
    *,
    version_label: str,
    title: str,
    summary: str,
    details_markdown: str | None,
    audience: str,
    status_value: str,
    area_tags: str | None,
    feature_flag_keys: str | None,
    published_at,
    created_by_user_id: int | None,
) -> ChangelogEntry:
    normalized_status = validate_changelog_status(status_value)
    entry = ChangelogEntry(
        version_label=version_label.strip(),
        title=title.strip(),
        summary=summary.strip(),
        details_markdown=details_markdown.strip() if details_markdown is not None and details_markdown.strip() else None,
        audience=validate_changelog_audience(audience),
        status=normalized_status,
        area_tags=_normalize_csv(area_tags),
        feature_flag_keys=_normalize_csv(feature_flag_keys),
        published_at=published_at or (utc_now() if normalized_status == "published" else None),
        created_by_user_id=created_by_user_id,
    )
    return _persist(session, entry)


def update_changelog_entry(
    session: Session,
    *,
    entry: ChangelogEntry,
    version_label: str | None = None,
    title: str | None = None,
    summary: str | None = None,
    details_markdown: str | None = None,
    audience: str | None = None,
    status_value: str | None = None,
    area_tags: str | None = None,
    feature_flag_keys: str | None = None,
    published_at=None,
    details_markdown_provided: bool = False,
    area_tags_provided: bool = False,
    feature_flag_keys_provided: bool = False,
    published_at_provided: bool = False,
) -> ChangelogEntry:
    if version_label is not None:
        entry.version_label = version_label.strip()
    if title is not None:
        entry.title = title.strip()
    if summary is not None:
        entry.summary = summary.strip()
    if details_markdown_provided:
        entry.details_markdown = details_markdown.strip() if details_markdown is not None and details_markdown.strip() else None
    if audience is not None:
        entry.audience = validate_changelog_audience(audience)
    if status_value is not None:
        entry.status = validate_changelog_status(status_value)
        if entry.status == "published" and entry.published_at is None:
            entry.published_at = utc_now()
    if area_tags_provided:
        entry.area_tags = _normalize_csv(area_tags)
    if feature_flag_keys_provided:
        entry.feature_flag_keys = _normalize_csv(feature_flag_keys)
    if published_at_provided:
        entry.published_at = published_at
    entry.updated_at = utc_now()
    return _persist(session, entry)


def publish_changelog_entry(session: Session, *, entry: ChangelogEntry) -> ChangelogEntry:
    entry.status = "published"
    if entry.published_at is None:
        entry.published_at = utc_now()
    entry.updated_at = utc_now()
    return _persist(session, entry)


def archive_changelog_entry(session: Session, *, entry: ChangelogEntry) -> ChangelogEntry:
    entry.status = "archived"
    entry.updated_at = utc_now()
    return _persist(session, entry)
