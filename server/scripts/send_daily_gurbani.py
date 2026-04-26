import os
import sys
import random
import logging

# Add parent directory to path to allow imports from server/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Shabad, PushToken
from notifications import send_push_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily_gurbani")

def send_daily_reflection():
    with app.app_context():
        # 1. Pick a random shabad
        count = Shabad.query.count()
        if count == 0:
            logger.warning("No shabads in database.")
            return
            
        random_index = random.randint(0, count - 1)
        shabad = Shabad.query.offset(random_index).first()
        
        if not shabad:
            logger.warning("Could not retrieve shabad.")
            return
            
        # 2. Get all push tokens
        tokens = [pt.token for pt in PushToken.query.all()]
        if not tokens:
            logger.info("No push tokens registered.")
            return
            
        # 3. Prepare message
        title = "☬ Daily Gurbani Reflection"
        # Translation or primary Gurmukhi
        body = f"{shabad.english_translation[:100]}...\n{shabad.gurmukhi}"
        
        # 4. Send
        logger.info(f"Sending daily reflection to {len(tokens)} users: {shabad.shabad_id}")
        res = send_push_notifications(tokens, title, body, data={"shabad_id": shabad.shabad_id})
        logger.info(f"Result: {res}")

if __name__ == "__main__":
    send_daily_reflection()
