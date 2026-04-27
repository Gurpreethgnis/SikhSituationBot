import logging
import requests
from typing import List, Optional, Union

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

def send_push_notifications(tokens: Union[str, List[str]], title: str, body: str, data: Optional[dict] = None):
    """
    Sends push notifications to Expo push tokens.
    
    :param tokens: A single token string or a list of tokens.
    :param title: The title of the notification.
    :param body: The message body.
    :param data: Optional JSON data to include.
    """
    if not tokens:
        return
        
    if isinstance(tokens, str):
        tokens = [tokens]
        
    # Expo limit: 100 messages per request
    # For MVP we just send them in one go if small, or we could chunk.
    payload = []
    for token in tokens:
        if not token.startswith("ExponentPushToken"):
            continue
        msg = {
            "to": token,
            "title": title,
            "body": body,
            "sound": "default"
        }
        if data:
            msg["data"] = data
        payload.append(msg)
        
    if not payload:
        return

    try:
        response = requests.post(
            EXPO_PUSH_URL,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        logger.info("Push notification sent: %s", result)
        return result
    except Exception as e:
        logger.error("Failed to send push notifications: %s", e)
        return None
