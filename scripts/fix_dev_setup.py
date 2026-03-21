"""
Fix local development setup when login fails.

This script:
1. Resets the database and reapplies migrations
2. Seeds demo data (including admin user with correct password)
3. Prints what to do next

Run from project root: python scripts/fix_dev_setup.py
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    print("Resetting database...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "reset_db.py")], check=True, cwd=ROOT)

    print("Seeding demo data...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_demo.py")], check=True, cwd=ROOT)

    print()
    print("=" * 60)
    print("Setup complete. Next steps:")
    print()
    print("1. RESTART your backend (stop it with Ctrl+C, then start again):")
    print("   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
    print()
    print("2. Log in with:")
    print("   Email:    admin@buddybug.local")
    print("   Password: Admin123!")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
