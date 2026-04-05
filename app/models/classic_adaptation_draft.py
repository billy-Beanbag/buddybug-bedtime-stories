from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClassicAdaptationDraft(SQLModel, table=True):
    """Internal-only Buddybug adaptation draft for a public-domain classic."""

    id: int | None = Field(default=None, primary_key=True)
    classic_source_id: int = Field(foreign_key="classicsource.id", index=True)
    project_id: int | None = Field(default=None, foreign_key="editorialproject.id", index=True)
    story_draft_id: int | None = Field(default=None, foreign_key="storydraft.id", index=True)
    preview_book_id: int | None = Field(default=None, foreign_key="book.id", index=True)
    adapted_title: str = Field(index=True)
    adapted_text: str
    adaptation_intensity: str = Field(default="light", index=True)
    adaptation_notes: str | None = None
    cameo_insertions_summary: str | None = None
    scene_seed_notes_json: str | None = None
    page_scene_data_json: str | None = None
    validation_status: str = Field(default="accepted", index=True)
    validation_warnings_json: str | None = None
    illustration_status: str = Field(default="not_started", index=True)
    review_status: str = Field(default="pending", index=True)
    editor_notes: str | None = None
    created_by_user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )
