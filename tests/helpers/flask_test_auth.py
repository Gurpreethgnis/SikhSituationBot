"""Create a test user and JWT for /ask and other protected Flask routes in unittest suites."""

import json
from typing import Any, Dict

from auth_utils import encode_token
from models import User, db


def ask_auth_headers(app, email: str = "unittest-ask-user@example.com") -> Dict[str, str]:
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if not u:
            u = User(email=email, is_active=True)
            db.session.add(u)
            db.session.commit()
        token = encode_token(u.id, u.email, bool(u.is_admin))
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def post_ask(client, app, payload: Dict[str, Any], **kwargs):
    return client.post("/ask", data=json.dumps(payload), headers=ask_auth_headers(app), **kwargs)
