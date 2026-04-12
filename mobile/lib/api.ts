/**
 * Flask base URL — aligned with `client/lib/api.js`:
 * - Use EXPO_PUBLIC_API_URL when set (and not the literal "same-origin").
 * - In development, default to http://localhost:5000 so local web + Flask work without a separate mobile/.env.
 * - Production / release builds must set EXPO_PUBLIC_API_URL (e.g. same value as NEXT_PUBLIC_API_URL on Vercel).
 */
export function apiBase(): string {
  const raw = (process.env.EXPO_PUBLIC_API_URL || '').trim();
  if (raw && raw.toLowerCase() !== 'same-origin') {
    return raw.replace(/\/$/, '');
  }
  if (__DEV__) {
    return 'http://localhost:5000';
  }
  return '';
}

/** Throws if there is no API base URL (release builds without EXPO_PUBLIC_API_URL). */
export function requireApiBase(): string {
  const base = apiBase();
  if (!base) {
    throw new Error(
      'No API base URL for this build. Set NEXT_PUBLIC_API_URL or FLASK_API_URL in the repo root .env (same as the web app), then run `cd mobile && npm run sync-env` and rebuild. Production mobile needs an absolute Flask URL (not same-origin).'
    );
  }
  return base;
}

/**
 * Parse a fetch Response as JSON. Surfaces HTML/plain-text error pages as readable errors
 * instead of "JSON Parse error: Unexpected character: N".
 */
export async function parseJsonResponse<T = Record<string, unknown>>(res: Response): Promise<T> {
  const text = await res.text();
  const trimmed = text.trim();
  if (!trimmed) {
    if (!res.ok) {
      throw new Error(`Request failed (${res.status} ${res.statusText || ''}). Empty response.`);
    }
    return {} as T;
  }
  const first = trimmed[0];
  if (first !== '{' && first !== '[' && first !== '"') {
    const preview = trimmed.slice(0, 200).replace(/\s+/g, ' ');
    throw new Error(
      `API returned non-JSON (${res.status}). Check EXPO_PUBLIC_API_URL and that the Flask server is running. Preview: ${preview}`
    );
  }
  try {
    return JSON.parse(trimmed) as T;
  } catch {
    const preview = trimmed.slice(0, 200).replace(/\s+/g, ' ');
    throw new Error(`Invalid JSON from API (${res.status}). Preview: ${preview}`);
  }
}

export function authHeaders(token?: string | null): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
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
];

export type GuidanceMode = 'guidance' | 'parmaan';
export type ParmaanDiscoveryType = 'similar' | 'topic' | 'dissimilar';
export type ParmaanComposerAction = 'ask' | 'line' | 'theme';

export const ASK_TIMEOUT_MS = 120_000;
