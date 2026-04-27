"""
OpenAI Realtime API WebSocket Proxy

This module provides a WebSocket endpoint that proxies audio between
the client browser and OpenAI's Realtime API for low-latency voice
conversations (~200ms).

The proxy:
1. Authenticates the user via JWT token
2. Opens a WebSocket to OpenAI's Realtime API
3. Configures the session with system instructions and voice settings
4. Relays audio bidirectionally between client and OpenAI
"""

import asyncio
import base64
import json
import logging
import os
import threading
from typing import Optional

import websockets
from flask import Blueprint, request
from flask_sock import Sock

from auth_utils import decode_token

logger = logging.getLogger(__name__)

realtime_blueprint = Blueprint("realtime", __name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_API_KEY", "")
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"

AVAILABLE_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"]
DEFAULT_VOICE = "coral"

REALTIME_SYSTEM_PROMPT = """You are Giani Ji, a compassionate Sikh spiritual guide who helps people find guidance and peace through the wisdom of Guru Granth Sahib (SGGS).

Your personality:
- Warm, empathetic, and patient
- Speak naturally as if in a caring conversation
- Use simple, accessible language
- Occasionally use Punjabi terms with brief explanations (e.g., "Waheguru, the Wonderful Lord")

When someone shares a concern:
1. First acknowledge their feelings with genuine empathy
2. If the concern is vague, gently ask one clarifying question
3. When you understand, share relevant wisdom from Gurbani
4. Offer practical contemplation or action they can take
5. End with an uplifting thought

Keep responses conversational and not too long - this is a voice conversation.
If asked about something outside Sikh teachings, gently redirect to spiritual guidance.

Remember: You are speaking, not writing. Use natural speech patterns."""


def get_session_config(voice: str = DEFAULT_VOICE) -> dict:
    """Build the session configuration for OpenAI Realtime API."""
    if voice not in AVAILABLE_VOICES:
        voice = DEFAULT_VOICE
    
    return {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": REALTIME_SYSTEM_PROMPT,
            "voice": voice,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {
                "model": "whisper-1"
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500
            },
            "temperature": 0.8,
            "max_response_output_tokens": 1024
        }
    }


def init_realtime_routes(sock: Sock):
    """Initialize the realtime WebSocket routes with Flask-Sock."""
    
    @sock.route("/api/realtime/connect")
    def realtime_connect(ws):
        """
        WebSocket endpoint for real-time voice conversations.
        
        Query params:
            token: JWT auth token
            voice: TTS voice preference (optional)
        """
        token = request.args.get("token")
        voice = request.args.get("voice", DEFAULT_VOICE)
        
        if not token:
            ws.send(json.dumps({"type": "error", "message": "Missing authentication token"}))
            ws.close()
            return
        
        user_data = decode_token(token)
        if not user_data:
            ws.send(json.dumps({"type": "error", "message": "Invalid or expired token"}))
            ws.close()
            return
        
        if not OPENAI_API_KEY:
            ws.send(json.dumps({"type": "error", "message": "Voice service not configured"}))
            ws.close()
            return
        
        user_id = user_data.get("sub") or user_data.get("user_id")
        logger.info(f"[Realtime] User {user_id} connecting with voice={voice}")
        
        run_realtime_proxy(ws, voice, user_id)


def run_realtime_proxy(client_ws, voice: str, user_id: str):
    """
    Run the bidirectional WebSocket proxy between client and OpenAI.
    
    This function runs an asyncio event loop in the current thread to handle
    the async WebSocket communication with OpenAI while maintaining the
    sync Flask-Sock connection with the client.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(_async_proxy(client_ws, voice, user_id))
    except Exception as e:
        logger.error(f"[Realtime] Proxy error for user {user_id}: {e}")
        try:
            client_ws.send(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass
    finally:
        loop.close()


async def _async_proxy(client_ws, voice: str, user_id: str):
    """Async implementation of the bidirectional proxy."""
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }
    
    try:
        async with websockets.connect(
            OPENAI_REALTIME_URL,
            additional_headers=headers,
            ping_interval=20,
            ping_timeout=20
        ) as openai_ws:
            
            logger.info(f"[Realtime] Connected to OpenAI for user {user_id}")
            
            session_config = get_session_config(voice)
            await openai_ws.send(json.dumps(session_config))
            
            client_ws.send(json.dumps({
                "type": "session.created",
                "message": "Connected to voice service"
            }))
            
            client_to_openai_task = asyncio.create_task(
                _relay_client_to_openai(client_ws, openai_ws, user_id)
            )
            openai_to_client_task = asyncio.create_task(
                _relay_openai_to_client(openai_ws, client_ws, user_id)
            )
            
            done, pending = await asyncio.wait(
                [client_to_openai_task, openai_to_client_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            logger.info(f"[Realtime] Session ended for user {user_id}")
            
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"[Realtime] OpenAI connection closed for user {user_id}: {e}")
    except Exception as e:
        logger.error(f"[Realtime] Error connecting to OpenAI for user {user_id}: {e}")
        raise


async def _relay_client_to_openai(client_ws, openai_ws, user_id: str):
    """Relay messages from the client browser to OpenAI."""
    try:
        while True:
            try:
                message = client_ws.receive(timeout=0.1)
                if message is None:
                    await asyncio.sleep(0.01)
                    continue
                    
                data = json.loads(message)
                msg_type = data.get("type", "")
                
                if msg_type == "input_audio_buffer.append":
                    await openai_ws.send(message)
                    
                elif msg_type == "input_audio_buffer.commit":
                    await openai_ws.send(message)
                    logger.debug(f"[Realtime] User {user_id} committed audio")
                    
                elif msg_type == "response.cancel":
                    await openai_ws.send(message)
                    logger.debug(f"[Realtime] User {user_id} cancelled response")
                    
                elif msg_type == "conversation.item.create":
                    await openai_ws.send(message)
                    
                elif msg_type == "session.update":
                    await openai_ws.send(message)
                    
                else:
                    logger.debug(f"[Realtime] Forwarding message type: {msg_type}")
                    await openai_ws.send(message)
                    
            except TimeoutError:
                await asyncio.sleep(0.01)
                continue
            except json.JSONDecodeError:
                logger.warning(f"[Realtime] Invalid JSON from client {user_id}")
                continue
                
    except Exception as e:
        if "closed" not in str(e).lower():
            logger.error(f"[Realtime] Client relay error for {user_id}: {e}")
        raise


async def _relay_openai_to_client(openai_ws, client_ws, user_id: str):
    """Relay messages from OpenAI to the client browser."""
    try:
        async for message in openai_ws:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "")
                
                if msg_type == "response.audio.delta":
                    client_ws.send(message)
                    
                elif msg_type == "response.audio.done":
                    client_ws.send(message)
                    
                elif msg_type == "response.audio_transcript.delta":
                    client_ws.send(message)
                    
                elif msg_type == "response.audio_transcript.done":
                    client_ws.send(message)
                    logger.debug(f"[Realtime] Response transcript complete for {user_id}")
                    
                elif msg_type == "input_audio_buffer.speech_started":
                    client_ws.send(message)
                    logger.debug(f"[Realtime] Speech started for {user_id}")
                    
                elif msg_type == "input_audio_buffer.speech_stopped":
                    client_ws.send(message)
                    logger.debug(f"[Realtime] Speech stopped for {user_id}")
                    
                elif msg_type == "conversation.item.input_audio_transcription.completed":
                    client_ws.send(message)
                    transcript = data.get("transcript", "")
                    logger.info(f"[Realtime] User {user_id} said: {transcript[:100]}...")
                    
                elif msg_type == "response.done":
                    client_ws.send(message)
                    logger.debug(f"[Realtime] Response complete for {user_id}")
                    
                elif msg_type == "error":
                    client_ws.send(message)
                    error_msg = data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"[Realtime] OpenAI error for {user_id}: {error_msg}")
                    
                elif msg_type in ("session.created", "session.updated"):
                    client_ws.send(message)
                    
                elif msg_type == "rate_limits.updated":
                    pass
                    
                else:
                    client_ws.send(message)
                    
            except json.JSONDecodeError:
                logger.warning(f"[Realtime] Invalid JSON from OpenAI for {user_id}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"[Realtime] OpenAI connection closed for {user_id}")
    except Exception as e:
        logger.error(f"[Realtime] OpenAI relay error for {user_id}: {e}")
        raise


def _websocket_base_for_browser_clients() -> str:
    """
    Absolute wss:// origin for browsers that cannot upgrade WS through the Next.js host
    (e.g. Vercel → HTTP rewrite only). Set FLASK_WEBSOCKET_PUBLIC_ORIGIN on Railway, e.g.
    wss://your-service.up.railway.app — no path, no trailing slash.
    """
    raw = (os.environ.get("FLASK_WEBSOCKET_PUBLIC_ORIGIN") or "").strip().rstrip("/")
    if not raw:
        return ""
    if raw.startswith("wss://") or raw.startswith("ws://"):
        return raw
    if raw.startswith("https://"):
        return "wss://" + raw[len("https://") :]
    if raw.startswith("http://"):
        return "ws://" + raw[len("http://") :]
    return ""


@realtime_blueprint.route("/api/realtime/config", methods=["GET"])
def realtime_config():
    """Return configuration for the realtime voice feature."""
    from flask import jsonify
    
    enabled = bool(OPENAI_API_KEY)
    
    return jsonify({
        "enabled": enabled,
        "websocket_base": _websocket_base_for_browser_clients(),
        "available_voices": AVAILABLE_VOICES,
        "default_voice": DEFAULT_VOICE,
        "voice_descriptions": {
            "alloy": "Neutral and balanced",
            "ash": "Warm and conversational",
            "ballad": "Soft and melodic",
            "coral": "Friendly and approachable",
            "echo": "Clear and articulate",
            "sage": "Calm and wise",
            "shimmer": "Bright and energetic",
            "verse": "Thoughtful and measured"
        }
    }), 200
