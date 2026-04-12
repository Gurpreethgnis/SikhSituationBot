'use client'

import React, { useState, useEffect } from 'react'
import { VOICE_CONSENT_KEY } from './voiceConfig.js'
import { apiBase } from '../../../lib/api'
import { useTranslation } from '../../contexts/TranslationContext.jsx'
import './VoiceButton.css'

/**
 * VoiceButton Component
 *
 * A simple button that triggers the full-screen VoiceMode overlay.
 * Handles consent modal and checks if voice is enabled on the server.
 *
 * Props:
 *   onActivate — () => void; called when user clicks to open voice mode
 *   disabled — boolean; bypasses all interaction if true
 */
export default function VoiceButton({ 
  onActivate,
  disabled = false
}) {
  const [serverVoiceEnabled, setServerVoiceEnabled] = useState(true)
  const [serverVoiceErrorVisible, setServerVoiceErrorVisible] = useState(false)
  const [consentShown, setConsentShown] = useState(() => {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(VOICE_CONSENT_KEY) === 'true'
    }
    return false
  })

  const { t } = useTranslation()
  const baseUrl = apiBase()

  useEffect(() => {
    fetch(`${baseUrl}/api/realtime/config`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.enabled === false) {
          setServerVoiceEnabled(false)
        }
      })
      .catch((err) => {
        console.warn('[VoiceButton] Could not fetch realtime config:', err)
        fetch(`${baseUrl}/api/voice/config`)
          .then((res) => res.json())
          .then((data) => {
            if (data && data.voice_enabled === false) {
              setServerVoiceEnabled(false)
            }
          })
          .catch(() => {})
      })
  }, [baseUrl])

  const handleClick = () => {
    if (!consentShown) return

    if (!serverVoiceEnabled) {
      setServerVoiceErrorVisible(true)
      return
    }

    onActivate?.()
  }

  const handleConsentAllow = () => {
    localStorage.setItem(VOICE_CONSENT_KEY, 'true')
    setConsentShown(true)
  }

  const handleConsentSkip = () => {
    setConsentShown(true)
  }

  if (serverVoiceErrorVisible) {
    return (
      <div className="voice-denied-strip">
        <span>{t('voiceNotConfigured') || 'Voice is not configured'}</span>
        <a onClick={() => setServerVoiceErrorVisible(false)}>{t('feedbackClose') || 'Close'}</a>
      </div>
    )
  }

  return (
    <>
      <button 
        className="voice-btn" 
        onClick={handleClick}
        disabled={disabled}
        aria-label="Start voice conversation"
        title="Voice conversation"
      >
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      </button>

      {!consentShown && (
        <div className="voice-consent-backdrop">
          <div className="voice-consent-modal">
            <h2>{t('voiceConsentTitle') || 'Voice Conversation'}</h2>
            <p>{t('voiceConsentText') || 'This feature uses your microphone for voice conversations. Your voice is processed in real-time and not stored.'}</p>
            <div className="voice-consent-modal__actions">
              <button className="voice-consent-modal__skip" onClick={handleConsentSkip}>
                {t('voiceConsentLater') || 'Not now'}
              </button>
              <button className="voice-consent-modal__allow" onClick={handleConsentAllow}>
                {t('voiceConsentAllow') || 'Allow'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
