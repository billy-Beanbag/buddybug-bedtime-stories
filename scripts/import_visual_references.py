from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import PROJECT_ROOT
from app.database import engine
from app.services.visual_reference_import_service import (
    build_character_bible_manifest,
    ensure_visual_reference_tables,
    import_entries,
    load_manifest_file,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import visual reference assets from the Artwork folder into Buddybug's asset base."
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        default=None,
        help="Optional path to a JSON manifest file. If omitted, auto-import the BuddyBug Character Bible.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the changes without writing to the database.")
    args = parser.parse_args()
    manifest = load_manifest_file(Path(args.manifest)) if args.manifest else build_character_bible_manifest()
    created_tables = ensure_visual_reference_tables()
    if created_tables:
        print("Creating missing database tables before import.")
    with Session(engine) as session:
        result = import_entries(session, manifest, dry_run=args.dry_run)
        if args.dry_run:
            print(f"Dry run complete. Scanned: {result.scanned}.")
        else:
            print(f"Import complete. Created: {result.created}. Updated: {result.updated}. Scanned: {result.scanned}.")


if __name__ == "__main__":
    main()
