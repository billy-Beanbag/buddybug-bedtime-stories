from collections.abc import Generator
import sqlite3
from urllib.parse import unquote, urlparse

from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL, DEBUG
import app.models  # noqa: F401


def is_sqlite_database_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def build_engine():
    connect_args = {"check_same_thread": False} if is_sqlite_database_url(DATABASE_URL) else {}
    return create_engine(
        DATABASE_URL,
        echo=DEBUG,
        connect_args=connect_args,
        pool_pre_ping=not is_sqlite_database_url(DATABASE_URL),
    )


engine = build_engine()


def _sqlite_database_path(database_url: str) -> str | None:
    if not is_sqlite_database_url(database_url):
        return None
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    parsed = urlparse(database_url)
    if parsed.path:
        return unquote(parsed.path.lstrip("/"))
    return None


def ensure_sqlite_schema_compatibility() -> list[str]:
    """Patch forward a local SQLite schema when the ORM has gained new nullable columns.

    This is intentionally limited to additive, non-destructive compatibility fixes for
    local developer databases that predate the latest model fields.
    """
    database_path = _sqlite_database_path(DATABASE_URL)
    if database_path is None:
        return []

    compatibility_columns: dict[str, list[tuple[str, str]]] = {
        "narrationvoice": [
            ("gender", "TEXT"),
            ("style", "TEXT"),
            ("accent", "TEXT"),
            ("gender_style", "TEXT"),
            ("age_style", "TEXT"),
            ("tone_style", "TEXT"),
            ("is_premium", "BOOLEAN NOT NULL DEFAULT 0"),
            ("is_active", "BOOLEAN NOT NULL DEFAULT 1"),
        ],
        "storydraft": [
            ("project_id", "INTEGER"),
            ("age_band", "TEXT NOT NULL DEFAULT '3-7'"),
            ("language", "TEXT NOT NULL DEFAULT 'en'"),
            ("content_lane_key", "TEXT DEFAULT 'bedtime_3_7'"),
            ("generation_source", "TEXT NOT NULL DEFAULT 'manual'"),
        ],
        "storyidea": [
            ("hook_type", "TEXT"),
            ("content_lane_key", "TEXT DEFAULT 'bedtime_3_7'"),
            ("supporting_characters", "TEXT"),
            ("series_key", "TEXT"),
            ("series_title", "TEXT"),
            ("generation_source", "TEXT NOT NULL DEFAULT 'manual'"),
        ],
        "book": [
            ("content_lane_key", "TEXT DEFAULT 'bedtime_3_7'"),
        ],
        "user": [
            ("is_editor", "BOOLEAN NOT NULL DEFAULT 0"),
            ("is_educator", "BOOLEAN NOT NULL DEFAULT 0"),
            ("organization_id", "INTEGER"),
            ("subscription_tier", "TEXT NOT NULL DEFAULT 'free'"),
            ("subscription_status", "TEXT NOT NULL DEFAULT 'none'"),
            ("subscription_expires_at", "DATETIME"),
            ("trial_ends_at", "DATETIME"),
            ("stripe_customer_id", "TEXT"),
            ("stripe_subscription_id", "TEXT"),
        ],
        "userstoryfeedback": [
            ("child_profile_id", "INTEGER"),
        ],
        "readingprogress": [
            ("child_profile_id", "INTEGER"),
        ],
        "reengagementsuggestion": [
            ("child_profile_id", "INTEGER"),
            ("related_book_id", "INTEGER"),
            ("state_key", "TEXT"),
            ("is_dismissed", "BOOLEAN NOT NULL DEFAULT 0"),
        ],
        "bedtimepack": [
            ("child_profile_id", "INTEGER"),
            ("language", "TEXT"),
            ("age_band", "TEXT"),
            ("content_lane_key", "TEXT"),
            ("prefer_narration", "BOOLEAN NOT NULL DEFAULT 0"),
            ("generated_reason", "TEXT"),
            ("active_date", "DATE"),
        ],
        "userlibraryitem": [
            ("child_profile_id", "INTEGER"),
            ("saved_for_offline", "BOOLEAN NOT NULL DEFAULT 0"),
            ("last_opened_at", "DATETIME"),
            ("downloaded_at", "DATETIME"),
        ],
        "readingplan": [
            ("child_profile_id", "INTEGER"),
            ("preferred_age_band", "TEXT"),
            ("preferred_language", "TEXT"),
            ("preferred_content_lane_key", "TEXT"),
            ("prefer_narration", "BOOLEAN NOT NULL DEFAULT 0"),
            ("sessions_per_week", "INTEGER NOT NULL DEFAULT 3"),
            ("target_days_csv", "TEXT"),
            ("bedtime_mode_preferred", "BOOLEAN NOT NULL DEFAULT 1"),
        ],
        "notificationevent": [
            ("child_profile_id", "INTEGER"),
        ],
        "supportticket": [
            ("child_profile_id", "INTEGER"),
            ("related_book_id", "INTEGER"),
            ("priority", "TEXT NOT NULL DEFAULT 'normal'"),
            ("assigned_to_user_id", "INTEGER"),
            ("source", "TEXT NOT NULL DEFAULT 'app'"),
            ("resolved_at", "DATETIME"),
        ],
        "analyticsevent": [
            ("child_profile_id", "INTEGER"),
        ],
        "dailystorysuggestion": [
            ("child_profile_id", "INTEGER"),
        ],
        "readalongsession": [
            ("child_profile_id", "INTEGER"),
            ("current_page_number", "INTEGER NOT NULL DEFAULT 0"),
            ("playback_state", "TEXT NOT NULL DEFAULT 'paused'"),
            ("language", "TEXT"),
            ("expires_at", "DATETIME"),
            ("ended_at", "DATETIME"),
        ],
        "readalongparticipant": [
            ("child_profile_id", "INTEGER"),
            ("last_seen_at", "DATETIME"),
        ],
        "readingstreaksnapshot": [
            ("child_profile_id", "INTEGER"),
            ("last_read_date", "DATE"),
        ],
        "earnedachievement": [
            ("child_profile_id", "INTEGER"),
        ],
        "datarequest": [
            ("child_profile_id", "INTEGER"),
            ("completed_at", "DATETIME"),
            ("output_url", "TEXT"),
            ("notes", "TEXT"),
        ],
        "childcomfortprofile": [
            ("child_profile_id", "INTEGER"),
            ("favorite_characters_csv", "TEXT"),
            ("favorite_moods_csv", "TEXT"),
            ("favorite_story_types_csv", "TEXT"),
            ("avoid_tags_csv", "TEXT"),
            ("preferred_language", "TEXT"),
            ("prefer_narration", "BOOLEAN NOT NULL DEFAULT 0"),
            ("prefer_shorter_stories", "BOOLEAN NOT NULL DEFAULT 0"),
            ("extra_calm_mode", "BOOLEAN NOT NULL DEFAULT 0"),
            ("bedtime_notes", "TEXT"),
        ],
        "childprofile": [
            ("content_lane_key", "TEXT"),
        ],
    }

    applied_changes: list[str] = []
    with sqlite3.connect(database_path) as connection:
        cursor = connection.cursor()
        for table_name, columns in compatibility_columns.items():
            existing_columns = {
                row[1]
                for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            }
            if not existing_columns:
                continue
            for column_name, column_sql in columns:
                if column_name in existing_columns:
                    continue
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")
                applied_changes.append(f"{table_name}.{column_name}")
        connection.commit()
    return applied_changes


def create_db_and_tables() -> None:
    """Create tables directly for local-only helpers and isolated tests."""
    SQLModel.metadata.create_all(engine)


def required_tables_exist(*table_names: str) -> bool:
    inspector = inspect(engine)
    return all(inspector.has_table(table_name) for table_name in table_names)


def get_session() -> Generator[Session, None, None]:
    """Provide a request-scoped database session."""
    with Session(engine) as session:
        yield session
