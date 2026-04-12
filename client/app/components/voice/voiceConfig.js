/**
 * voiceConfig.js
 * Shared configuration constants for the voice feature.
 * Import these into hooks and components — do not hardcode values elsewhere.
 */

/** Default OpenAI Realtime API voice. coral is friendly and approachable. */
export const DEFAULT_VOICE = 'coral'

/** Available Realtime API TTS voices. */
export const AVAILABLE_VOICES = ['alloy', 'ash', 'ballad', 'coral', 'echo', 'sage', 'shimmer', 'verse']

/** BCP-47 language codes supported for Whisper STT. */
export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'ar', label: 'العربية' },
  { code: 'pt', label: 'Português' },
  { code: 'ru', label: 'Русский' },
]

/**
 * RMS amplitude threshold (0–1) above which the barge-in logic
 * considers the user to be speaking during TTS playback.
 * Lower = more sensitive. 0.015 avoids triggering on ambient noise.
 */
export const BARGE_IN_THRESHOLD = 0.015

/** Maximum recording duration in milliseconds (60 s = Whisper max). */
export const MAX_RECORDING_MS = 60_000

/** LocalStorage key for one-time privacy consent modal. */
export const VOICE_CONSENT_KEY = 'voice_consent_shown'

/** Voice state machine states. */
export const VOICE_STATE = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  PROCESSING: 'PROCESSING',
  SPEAKING: 'SPEAKING',
}
