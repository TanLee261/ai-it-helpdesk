from __future__ import annotations

import getpass
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.models import User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.security.passwords import hash_password, validate_new_password  # noqa: E402


def main() -> None:
    username = input("Admin username: ").strip().lower()
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password (12+ chars, letters and numbers): ")
    try:
        validate_new_password(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    with SessionLocal() as db:
        if db.query(User.id).filter(User.role == "admin").first():
            raise SystemExit("An admin account already exists; refusing to create another bootstrap admin.")
        if db.query(User.id).filter((User.username == username) | (User.email == email)).first():
            raise SystemExit("Username or email already exists.")
        db.add(User(
            username=username, email=email, full_name=full_name, role="admin",
            password_hash=hash_password(password), is_active=True, must_change_password=False,
        ))
        db.commit()
    print(f"Created initial admin account: {username}")


if __name__ == "__main__":
    main()
