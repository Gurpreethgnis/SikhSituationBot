const API_URL = process.env.EXPO_PUBLIC_API_URL || '';

export function apiBase(): string {
  return API_URL.replace(/\/$/, '');
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
