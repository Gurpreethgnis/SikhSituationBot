"""Create a test user and JWT for /ask and other protected Flask routes in unittest suites."""

import json
from datetime import datetime
from typing import Any, Dict

from auth_utils import encode_token
from models import User, db


def _persona_from_birth_year(birth_year: int) -> str:
    y = int(birth_year)
    now_y = datetime.utcnow().year
    age = now_y - y
    if age < 13:
        return "child"
    if age < 18:
        return "teen"
    return "adult"


def ask_auth_headers(app, email: str = "unittest-ask-user@example.com", birth_year: int = 1990) -> Dict[str, str]:
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(
                email=email,
                is_active=True,
                birth_year=birth_year,
                preferred_persona=_persona_from_birth_year(birth_year),
                persona_source="profile",
            )
            db.session.add(u)
            db.session.commit()
        elif u.birth_year is None:
            u.birth_year = birth_year
            u.preferred_persona = _persona_from_birth_year(birth_year)
            u.persona_source = "profile"
            db.session.commit()
        token = encode_token(u.id, u.email, bool(u.is_admin))
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def post_ask(client, app, payload: Dict[str, Any], **kwargs):
    return client.post("/ask", data=json.dumps(payload), headers=ask_auth_headers(app), **kwargs)
