import sys
import os

# Add the server directory to the path so we can import from it
sys.path.append(os.path.join(os.getcwd(), 'server'))

from app import db, app
from models import Shabad

with app.app_context():
    try:
        from sqlalchemy import text
        db.session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        db.session.commit()
        print("Extension vector created or already exists.")
    except Exception as e:
        print(f"Vector extension error: {e}")
        db.session.rollback()
        
    db.create_all()
    print("Database tables created successfully.")
