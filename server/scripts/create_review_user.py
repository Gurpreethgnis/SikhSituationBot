#!/usr/bin/env python3
"""
Create or update a database user for App Store / QA email+password sign-in.

Run on the Flask host (e.g. Railway) where DATABASE_URL is set:

  cd server && python scripts/create_review_user.py --email you@example.com --generate-password

Or set a password explicitly (8+ characters):

  python scripts/create_review_user.py --email you@example.com --password 'YourSecurePass123!'

Use the printed email + password in App Store Connect (Sign-in required).
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys

# server/ is on path when run as: python scripts/create_review_user.py from server/
_SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from auth_utils import hash_password  # noqa: E402
from models import User, db  # noqa: E402


def _load_app():
    from app import app as flask_app

    return flask_app


def main() -> int:
    p = argparse.ArgumentParser(description="Create/update review test user")
    p.add_argument(
        "--email",
        default=os.environ.get("REVIEW_USER_EMAIL", "appreview@gianiji.com"),
        help="Login email (default: appreview@gianiji.com or REVIEW_USER_EMAIL)",
    )
    p.add_argument(
        "--password",
        default=os.environ.get("REVIEW_USER_PASSWORD") or None,
        help="Password (8+ chars). If omitted, use --generate-password or REVIEW_USER_PASSWORD",
    )
    p.add_argument(
        "--generate-password",
        action="store_true",
        help="Generate a strong password and print it (recommended)",
    )
    p.add_argument(
        "--no-admin",
        action="store_true",
        help="Do not set is_admin=True (default: grant admin for full review)",
    )
    p.add_argument(
        "--birth-year",
        type=int,
        default=1990,
        help="Set birth year so onboarding gate is satisfied (default: 1990)",
    )
    args = p.parse_args()

    email = (args.email or "").strip().lower()
    if not email:
        print("error: email required", file=sys.stderr)
        return 1

    password = args.password
    if args.generate_password:
        password = secrets.token_urlsafe(18)
    if not password or len(password) < 8:
        print("error: password must be at least 8 characters (use --generate-password or --password)", file=sys.stderr)
        return 1

    app = _load_app()
    is_admin = not args.no_admin

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = hash_password(password)
            user.is_active = True
            user.is_admin = is_admin
            if user.birth_year is None:
                user.birth_year = args.birth_year
                user.preferred_persona = "adult"
                user.persona_source = "profile"
            db.session.commit()
            action = "updated"
        else:
            user = User(
                email=email,
                name="App Review",
                password_hash=hash_password(password),
                is_admin=is_admin,
                is_active=True,
                birth_year=args.birth_year,
                preferred_persona="adult",
                persona_source="profile",
            )
            db.session.add(user)
            db.session.commit()
            action = "created"

    print(f"OK: {action} user id={user.id}")
    print("")
    print("App Store Connect → App Review Information → Sign-in required:")
    print(f"  User name: {email}")
    print(f"  Password:  {password}")
    print("")
    print("Notes: use Email on the login screen (not Google). Rotate this password after review if you like.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
