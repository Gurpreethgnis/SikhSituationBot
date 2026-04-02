'use client'

import './VoiceStatusBar.css'
import { useTranslation } from '../../contexts/TranslationContext.jsx'


/**
 * VoiceStatusBar
 *
 * Pure display component. Receives voiceState and transcript as props.
 * Uses aria-live="polite" so screen readers announce state transitions
 * without interrupting ongoing speech.
 *
 * Props:
 *   voiceState  — 'IDLE' | 'LISTENING' | 'PROCESSING' | 'SPEAKING'
 *   transcript  — string | null, shown after STT returns (PROCESSING / SPEAKING)
 */
export default function VoiceStatusBar({ voiceState = 'IDLE', transcript }) {
  const { t } = useTranslation()
  const LABELS = {
    IDLE: '',
    LISTENING: t('voiceListening'),
    PROCESSING: t('voiceProcessing'),
    SPEAKING: t('voiceSpeaking'),
  }
  const label = LABELS[voiceState] || ''
  const showTranscript = transcript && (voiceState === 'PROCESSING' || voiceState === 'SPEAKING')

  return (
    <div
      className="voice-status-bar"
      data-state={voiceState}
      role="status"
      aria-live="polite"
      aria-label={label || 'Voice inactive'}
      aria-hidden={voiceState === 'IDLE'}
    >
      <span className="voice-status-bar__dot" aria-hidden />
      <span className="voice-status-bar__label">{label}</span>
      {showTranscript && (
        <span className="voice-status-bar__transcript" title={transcript}>
          "{transcript}"
        </span>
      )}
    </div>
  )
}
