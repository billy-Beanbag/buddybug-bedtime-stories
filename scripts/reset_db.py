from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from sqlmodel import SQLModel

from app.database import engine


def main() -> None:
    SQLModel.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, cwd=ROOT)
    print("Local Buddybug database reset complete.")
    print("This helper is for local development only.")
    print("Next step: run `python scripts/seed_demo.py` to repopulate demo data.")


if __name__ == "__main__":
    main()
