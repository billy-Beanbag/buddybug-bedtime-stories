from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session, select

from app.database import engine
from app.models import Book
from app.utils.dev_seed import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    DEMO_FREE_EMAIL,
    DEMO_FREE_PASSWORD,
    DEMO_PREMIUM_EMAIL,
    DEMO_PREMIUM_PASSWORD,
    seed_demo_environment,
)


def main() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=ROOT)
    with Session(engine) as session:
        result = seed_demo_environment(session)
        book_count = len(list(session.exec(select(Book)).all()))
        draft_id = result.story_draft.id
        draft_title = result.story_draft.title
        page_count = len(result.story_pages)
        illustration_count = len(result.illustrations)
        sample_book_id = result.book.id
        sample_book_title = result.book.title
        story_idea_count = len(result.story_ideas)
        audio_seeded = result.audio is not None

    print("Buddybug demo data seeded.")
    print("")
    print("Demo credentials")
    print(f"- Admin:   {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")
    print(f"- Premium: {DEMO_PREMIUM_EMAIL} / {DEMO_PREMIUM_PASSWORD}")
    print(f"- Free:    {DEMO_FREE_EMAIL} / {DEMO_FREE_PASSWORD}")
    print("")
    print("Content summary")
    print(f"- Story ideas: {story_idea_count}")
    print(f"- Demo draft: {draft_id} - {draft_title}")
    print(f"- Story pages: {page_count}")
    print(f"- Illustrations: {illustration_count} approved")
    print(f"- Books created: {book_count}")
    print(f"- Sample book: {sample_book_id} - {sample_book_title}")
    print(f"- Audio seeded: {'yes' if audio_seeded else 'no'}")


if __name__ == "__main__":
    main()
