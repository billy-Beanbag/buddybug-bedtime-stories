"""
Archive the Verity and the Missing Blanket Trail book so it no longer appears in the public library.
Run from project root: python scripts/archive_verity_book.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session, select

from app.database import engine
from app.models import Book
from app.services.review_service import utc_now


def main() -> None:
    with Session(engine) as session:
        book = session.exec(
            select(Book).where(Book.title == "Verity and the Missing Blanket Trail")
        ).first()
        if not book:
            print("Book 'Verity and the Missing Blanket Trail' not found.")
            return
        book.published = False
        book.publication_status = "archived"
        book.updated_at = utc_now()
        session.add(book)
        session.commit()
        session.refresh(book)
        print(f"Archived book id={book.id}: {book.title}")
        print("It will no longer appear in the public library.")


if __name__ == "__main__":
    main()
