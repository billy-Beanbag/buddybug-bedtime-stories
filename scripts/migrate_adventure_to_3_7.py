#!/usr/bin/env python3
"""Migrate existing adventure stories (8-12) to age band 3-7. Run once to update library."""
import sys
from pathlib import Path

# Ensure app is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlmodel import Session, select

from app.database import engine
from app.models import Book, BookDiscoveryMetadata, StoryDraft, StoryIdea
from app.utils.seed_content_lanes import STORY_ADVENTURES_8_12_LANE_KEY


def migrate() -> None:
    with Session(engine) as session:
        # Story ideas: adventure lane or 8-12 -> 3-7
        ideas = session.exec(
            select(StoryIdea).where(
                (StoryIdea.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY)
                | (StoryIdea.age_band == "8-12")
            )
        ).all()
        for idea in ideas:
            idea.age_band = "3-7"
            session.add(idea)
        ideas_count = len(ideas)

        # Story drafts: adventure lane or 8-12 -> 3-7
        drafts = session.exec(
            select(StoryDraft).where(
                (StoryDraft.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY)
                | (StoryDraft.age_band == "8-12")
            )
        ).all()
        for draft in drafts:
            draft.age_band = "3-7"
            session.add(draft)
        drafts_count = len(drafts)

        # Books: adventure lane or 8-12 -> 3-7
        books = session.exec(
            select(Book).where(
                (Book.content_lane_key == STORY_ADVENTURES_8_12_LANE_KEY)
                | (Book.age_band == "8-12")
            )
        ).all()
        for book in books:
            book.age_band = "3-7"
            session.add(book)
        books_count = len(books)

        # BookDiscoveryMetadata: sync with book age_band
        for book in books:
            meta = session.exec(
                select(BookDiscoveryMetadata).where(BookDiscoveryMetadata.book_id == book.id)
            ).first()
            if meta and meta.age_band == "8-12":
                meta.age_band = "3-7"
                session.add(meta)

        session.commit()
        print(
            f"Migrated: {ideas_count} story ideas, {drafts_count} drafts, {books_count} books to age band 3-7."
        )


if __name__ == "__main__":
    migrate()
