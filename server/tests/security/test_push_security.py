import os
import sys
import pytest
from unittest.mock import patch

# Setup environment for testing
os.environ['TESTING'] = 'true'
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL_TEST'] = 'sqlite:///:memory:'

# Import app components AFTER mocking the db types if needed
# (Already handled in test_sql_injection.py, but for standalone it's better)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import User
from auth_utils import encode_token

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # Create an admin and a normal user
            admin = User(email="admin@example.com", name="Admin", is_admin=True, is_active=True)
            user = User(email="user@example.com", name="User", is_admin=False, is_active=True)
            db.session.add_all([admin, user])
            db.session.commit()
            
            app.config['MOCK_ADMIN_TOKEN'] = encode_token(admin.id, admin.email, is_admin=True)
            app.config['MOCK_USER_TOKEN'] = encode_token(user.id, user.email, is_admin=False)
        yield client

def test_push_all_blocked_for_non_admins(client):
    """Verify that a regular user cannot send a broadcast notification."""
    token = app.config['MOCK_USER_TOKEN']
    resp = client.post('/api/admin/push-all', 
                       headers={'Authorization': f'Bearer {token}'},
                       json={'title': 'Evil', 'body': 'Notification'})
    assert resp.status_code == 403
    assert "Admin rights required" in resp.get_json()['error']

def test_push_single_blocked_for_non_admins(client):
    """Verify that a regular user cannot send a notification to a specific user."""
    token = app.config['MOCK_USER_TOKEN']
    resp = client.post('/api/admin/push-single', 
                       headers={'Authorization': f'Bearer {token}'},
                       json={'user_id': 1, 'title': 'Evil', 'body': 'Notification'})
    assert resp.status_code == 403
    assert "Admin rights required" in resp.get_json()['error']

def test_push_all_allowed_for_admins(client):
    """Verify that an admin can trigger the endpoint (even if it 404s/fails later due to no tokens)."""
    token = app.config['MOCK_ADMIN_TOKEN']
    with patch('notifications.send_push_notification') as mock_send:
        resp = client.post('/api/admin/push-all', 
                           headers={'Authorization': f'Bearer {token}'},
                           json={'title': 'Hello', 'body': 'World'})
        # Should NOT be 403. Might be 200 (Success) or 400 (if body/title missing)
        assert resp.status_code != 403
