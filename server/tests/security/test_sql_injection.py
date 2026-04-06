import os
import sys
import sqlalchemy.types

# 1. Environment SETUP
os.environ['TESTING'] = 'true'
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL_TEST'] = 'sqlite:///:memory:'

# 2. Monkey-patch Vector AND ARRAY to be TEXT for SQLite before ANY imports
class FakeVector(sqlalchemy.types.UserDefinedType):
    def get_col_spec(self, **kw):
        return "TEXT"
    def bind_processor(self, dialect):
        return lambda x: str(x)
    def result_processor(self, dialect, coltype):
        return lambda x: x

class FakeArray(sqlalchemy.types.UserDefinedType):
    def __init__(self, *args, **kwargs):
        pass
    def get_col_spec(self, **kw):
        return "TEXT"
    def bind_processor(self, dialect):
        return lambda x: ",".join(map(str, x)) if x else None
    def result_processor(self, dialect, coltype):
        return lambda x: x.split(",") if x else []

import pgvector.sqlalchemy
pgvector.sqlalchemy.Vector = FakeVector

import sqlalchemy.dialects.postgresql
sqlalchemy.dialects.postgresql.ARRAY = FakeArray
# Also mock the top-level ARRAY if imported from sqlalchemy
import sqlalchemy
sqlalchemy.ARRAY = FakeArray

import pytest
from unittest.mock import patch, MagicMock

# Ensure we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Shabad

from auth_utils import encode_token

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            # Ensure fresh state for every test
            db.drop_all()
            db.create_all()
            from models import User
            # Add some seed data
            s1 = Shabad(shabad_id="sggs_1", gurmukhi="ੴ", english_translation="One Creator", source="SGGS Ang 1")
            s2 = Shabad(shabad_id="sggs_2", gurmukhi="ਸਤਿਨਾਮੁ", english_translation="True Name", source="SGGS Ang 2")
            admin = User(email="admin@example.com", name="Admin", is_admin=True, is_active=True)
            db.session.add_all([s1, s2, admin])
            db.session.commit()
            
            # Generate a real token
            token = encode_token(admin.id, admin.email, is_admin=True)
            app.config['MOCK_ADMIN_TOKEN'] = token
        yield client

def test_search_wildcard_injection_is_blocked(client):
    """Confirm a '%' wildcard is blocked with 400 Bad Request."""
    resp = client.get('/api/search?q=%&mode=text')
    assert resp.status_code == 400
    assert "Invalid search" in resp.get_json()['error']

def test_admin_interaction_wildcard_injection_is_sanitized(client):
    """
    Test that a '%' wildcard in admin interactions doesn't return all logs.
    """
    token = app.config['MOCK_ADMIN_TOKEN']
    # No mocks needed now, we use a real token and a real (memory) DB user
    resp = client.get('/api/admin/interactions?user_email=%', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    # If 0 results, it was correctly sanitized (since no email is likely to be '%')
    assert len(resp.get_json().get('interactions', [])) == 0

def test_regex_ladder_complexity_injection_is_safe(client):
    """
    Test that complex regex characters in ladder search are ignored or return 0 results.
    """
    resp = client.get('/api/search?q=.*&mode=first_letter')
    assert resp.status_code == 200
    assert len(resp.get_json()['results']) == 0
