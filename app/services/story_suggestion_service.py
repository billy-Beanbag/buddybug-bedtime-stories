from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from app.models import StorySuggestion


@dataclass(frozen=True)
class StorySuggestionReference:
    title: str | None
    brief: str
    desired_outcome: str | None
    inspiration_notes: str | None
    avoid_notes: str | None


def list_story_suggestion_references(
    session: Session,
    *,
    age_band: str,
    limit: int = 3,
) -> list[StorySuggestionReference]:
    """Return approved, reusable parent suggestions as editorial guidance."""
    statement = (
        select(StorySuggestion)
        .where(
            StorySuggestion.age_band == age_band,
            StorySuggestion.status == "approved",
            StorySuggestion.allow_reference_use.is_(True),
            StorySuggestion.approved_as_reference.is_(True),
        )
        .order_by(StorySuggestion.updated_at.desc())
        .limit(limit)
    )
    items = list(session.exec(statement).all())
    return [
        StorySuggestionReference(
            title=item.title,
            brief=item.brief,
            desired_outcome=item.desired_outcome,
            inspiration_notes=item.inspiration_notes,
            avoid_notes=item.avoid_notes,
        )
        for item in items
    ]


def build_story_suggestion_guidance_lines(
    references: list[StorySuggestionReference],
) -> list[str]:
    lines: list[str] = []
    for index, reference in enumerate(references, start=1):
        prefix = f"Approved parent suggestion {index}"
        if reference.title:
            prefix += f" ({reference.title})"
        lines.append(f"{prefix}: {reference.brief}")
        if reference.desired_outcome:
            lines.append(f"Desired outcome {index}: {reference.desired_outcome}")
        if reference.inspiration_notes:
            lines.append(f"Include if helpful {index}: {reference.inspiration_notes}")
        if reference.avoid_notes:
            lines.append(f"Avoid if possible {index}: {reference.avoid_notes}")
    return lines
