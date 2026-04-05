from __future__ import annotations

from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models import ClassicSource, User
from app.utils.public_domain_classics_catalog import PUBLIC_DOMAIN_CLASSICS


def _get_import_user(session: Session) -> User:
    user = session.exec(select(User).where(User.email == "admin@buddybug.local")).first()
    if user is None:
        raise RuntimeError("Demo admin user admin@buddybug.local was not found in the local database.")
    return user


def _upsert_classic_source(session: Session, *, current_user: User, title: str, source_text: str, source_url: str, source_author: str, source_origin_notes: str) -> str:
    existing = session.exec(select(ClassicSource).where(ClassicSource.title == title)).first()
    if existing is None:
        session.add(
            ClassicSource(
                title=title,
                source_text=source_text.strip(),
                source_url=source_url.strip(),
                public_domain_verified=True,
                source_author=source_author.strip(),
                source_origin_notes=source_origin_notes.strip(),
                import_status="imported",
                created_by_user_id=current_user.id,
            )
        )
        session.commit()
        return "created"
    existing.source_text = source_text.strip()
    existing.source_url = source_url.strip()
    existing.public_domain_verified = True
    existing.source_author = source_author.strip()
    existing.source_origin_notes = source_origin_notes.strip()
    if existing.import_status == "archived":
        existing.import_status = "imported"
    session.add(existing)
    session.commit()
    return "updated"


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        current_user = _get_import_user(session)
        created = 0
        updated = 0
        for entry in PUBLIC_DOMAIN_CLASSICS:
            result = _upsert_classic_source(
                session,
                current_user=current_user,
                title=entry.title,
                source_text=entry.source_text,
                source_url=entry.source_url,
                source_author=entry.source_author,
                source_origin_notes=entry.source_origin_notes,
            )
            if result == "created":
                created += 1
            else:
                updated += 1
        print(f"Imported classics complete: created={created}, updated={updated}, total_catalog={len(PUBLIC_DOMAIN_CLASSICS)}")


if __name__ == "__main__":
    main()
