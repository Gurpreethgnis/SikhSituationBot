/**
 * Base URL for browser → Flask API.
 *
 * Production gotcha: env vars are baked in at `next build`. If NEXT_PUBLIC_API_URL is missing,
 * the old default was http://localhost:5000 — the user's browser then talks to their own PC,
 * not Railway, so Flask logs stay empty.
 *
 * Fix either:
 * 1) Set NEXT_PUBLIC_API_URL=https://your-flask-host (CORS must allow your Next origin), or
 * 2) Set FLASK_API_URL on the Next.js host at build time and leave NEXT_PUBLIC_API_URL unset
 *    (or set to "same-origin"). Next.js rewrites then proxy /ask and /api/* to Flask same-origin.
 *
 * Realtime voice WebSockets: Vercel rewrites are HTTP-only. Set NEXT_PUBLIC_API_URL to your Flask
 * HTTPS URL so the client opens wss:// to the same host, or set FLASK_WEBSOCKET_PUBLIC_ORIGIN on
 * Flask and return it from GET /api/realtime/config (see server/realtime_routes.py).
 */
export function apiBase() {
  const raw = (process.env.NEXT_PUBLIC_API_URL || '').trim()
  if (raw && raw.toLowerCase() !== 'same-origin') {
    return raw.replace(/\/$/, '')
  }
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:5000'
  }
  /* Production: same-origin; requires FLASK_API_URL rewrites in next.config.mjs */
  return ''
}

/**
 * WebSocket origin for Flask realtime voice (no path).
 * Vercel HTTP rewrites do not upgrade browser WebSockets to Railway — the client must open
 * wss:// directly to the Flask host when the UI is served from a different origin.
 */
export function realtimeWsBaseFromEnv() {
  const raw = (process.env.NEXT_PUBLIC_API_URL || '').trim()
  if (!raw || raw.toLowerCase() === 'same-origin') {
    return ''
  }
  try {
    const u = new URL(raw.includes('://') ? raw : `https://${raw}`)
    const wsProto = u.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsProto}//${u.host}`
  } catch {
    return ''
  }
}

export function authHeaders(token) {
  const h = { 'Content-Type': 'application/json' }
  if (token) h.Authorization = `Bearer ${token}`
  return h
}

export const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'ar', label: 'العربية' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'pt', label: 'Português' },
  { code: 'ru', label: 'Русский' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' },
]
