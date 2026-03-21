#!/usr/bin/env python3
"""Delete a workflow record (book, draft, idea) directly via database. Use when the HTTP API isn't working."""
import argparse
from sqlmodel import Session

from app.database import engine
from app.services.admin_service import delete_workflow_record


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete a workflow record and all dependencies")
    parser.add_argument("--book-id", type=int, help="Book ID to delete")
    parser.add_argument("--draft-id", type=int, help="Draft ID to delete")
    parser.add_argument("--idea-id", type=int, help="Idea ID to delete")
    args = parser.parse_args()

    if not any([args.book_id, args.draft_id, args.idea_id]):
        parser.error("At least one of --book-id, --draft-id, or --idea-id is required")

    with Session(engine) as session:
        delete_workflow_record(
            session,
            book_id=args.book_id,
            draft_id=args.draft_id,
            idea_id=args.idea_id,
        )
    print("Workflow record deleted successfully.")


if __name__ == "__main__":
    main()
