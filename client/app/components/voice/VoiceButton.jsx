'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { 
  DEFAULT_VOICE, 
  AVAILABLE_VOICES, 
  SUPPORTED_LANGUAGES, 
  VOICE_STATE, 
  VOICE_CONSENT_KEY 
} from './voiceConfig.js'
import { useVoiceRecorder } from './useVoiceRecorder.js'
import { useAudioPlayer } from './useAudioPlayer.js'
import { apiBase } from '../../../lib/api'
import { useTranslation } from '../../contexts/TranslationContext.jsx'
import './VoiceButton.css'

/**
 * VoiceButton Component
 *
 * This component provides the main interactive trigger for voice STT/TTS.
 * It manages a set of sub-states (IDLE, LISTENING, PROCESSING, SPEAKING).
 *
 * Props:
 *   onTranscript — (text) => void; called when STT succeeds.
 *   onStateChange — (state) => void; called when the voice state changes.
 *   assistantResponse — string | null; watch this to trigger TTS.
 *   disabled — boolean; bypasses all interaction if true.
 *   language — string; current user language choice for STT hint.
 */
export default function VoiceButton({ 
  onTranscript, 
  onStateChange, 
  assistantResponse, 
  disabled: disabledProp = false,
  language = 'en'
}) {
  const [internalState, setInternalState] = useState(VOICE_STATE.IDLE)
  const [handsFree, setHandsFree] = useState(false)
  const [lastProcessedResponse, setLastProcessedResponse] = useState(null)
  const [micDenied, setMicDenied] = useState(false)
  const [serverVoiceEnabled, setServerVoiceEnabled] = useState(true)
  const [serverVoiceErrorVisible, setServerVoiceErrorVisible] = useState(false)
  const [transcribeError, setTranscribeError] = useState(null)
  // Track if we're in an active voice conversation session (user initiated voice)
  const [voiceSessionActive, setVoiceSessionActive] = useState(false)
  // Track if we're waiting for assistant response to speak
  const [awaitingResponse, setAwaitingResponse] = useState(false)

  const { isRecording, startRecording, stopRecording, audioBlob, error: recorderError, clearBlob } = useVoiceRecorder({
    vadEnabled: handsFree,
    onSilence: () => {
      if (internalState === VOICE_STATE.LISTENING) {
        stopRecording()
      }
    },
    onRecordingComplete: (blob) => {
      if (internalState === VOICE_STATE.LISTENING) {
        handleTranscribe(blob)
        clearBlob()
      }
    }
  })
  const { isPlaying, play, stop: stopAudio, interrupt: interruptAudio } = useAudioPlayer()

  const { t } = useTranslation()
  const baseUrl = apiBase()

  // --- Handlers for parents ---
  const updateState = useCallback((next) => {
    setInternalState(next)
    onStateChange?.(next)
  }, [onStateChange])

  // --- Initial check for consent (lazy initialization) ---
  const [consentShown, setConsentShown] = useState(() => {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(VOICE_CONSENT_KEY) === 'true'
    }
    return false
  })

  // --- Check Backend Configuration ---
  useEffect(() => {
    fetch(`${baseUrl}/api/voice/config`)
      .then((res) => res.json())
      .then((data) => {
        if (data && data.voice_enabled === false) {
          setServerVoiceEnabled(false)
        }
      })
      .catch((err) => {
        console.warn('[VoiceButton] Could not fetch voice config:', err)
      })
  }, [baseUrl])

  // --- STT trigger now handled by onRecordingComplete ---

  // --- Handle Recorder Errors ---
  useEffect(() => {
    if (recorderError === 'mic_denied') {
      setMicDenied(true)
      updateState(VOICE_STATE.IDLE)
    } else if (recorderError) {
      console.error('[VoiceButton] Recorder error:', recorderError)
      updateState(VOICE_STATE.IDLE)
    }
  }, [recorderError, updateState])

  // --- Handle Assistant Response Changes (TTS Trigger) ---
  useEffect(() => {
    if (assistantResponse && assistantResponse !== lastProcessedResponse) {
      setLastProcessedResponse(assistantResponse)
      // Speak if we're in a voice session and waiting for response
      // This allows TTS even when state has transitioned to IDLE after transcription
      if (voiceSessionActive && awaitingResponse) {
        setAwaitingResponse(false)
        handleSynthesize(assistantResponse)
      }
    }
  }, [assistantResponse, lastProcessedResponse, voiceSessionActive, awaitingResponse])

  // --- Sync component state with audio playback ---
  useEffect(() => {
    if (isPlaying) {
      updateState(VOICE_STATE.SPEAKING)
    } else if (internalState === VOICE_STATE.SPEAKING) {
      // Bot finished speaking - if hands-free mode is on, auto-restart listening
      if (handsFree && voiceSessionActive) {
        startRecording()
        updateState(VOICE_STATE.LISTENING)
      } else {
        updateState(VOICE_STATE.IDLE)
      }
    }
  }, [isPlaying, internalState, updateState, handsFree, voiceSessionActive, startRecording])

  const handleTranscribe = async (blob) => {
    updateState(VOICE_STATE.PROCESSING)
    try {
      const formData = new FormData()
      formData.append('audio', blob, 'query.webm')
      formData.append('language', language)

      const res = await fetch(`${baseUrl}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.message || 'STT failed')
      }
      const data = await res.json()
      
      if (data.transcript) {
        // Mark that we're waiting for assistant response to speak it
        setAwaitingResponse(true)
        // Send to parent immediately - parent should trigger handleSend
        onTranscript?.(data.transcript)
        // Show processing state while waiting for response
        updateState(VOICE_STATE.PROCESSING)
      } else {
        updateState(VOICE_STATE.IDLE)
      }
    } catch (err) {
      console.error('[VoiceButton] Transcribe error:', err.message)
      setTranscribeError(err.message)
      updateState(VOICE_STATE.IDLE)
    }
  }

  const handleSynthesize = async (text) => {
    if (!text) return
    updateState(VOICE_STATE.PROCESSING)
    try {
      const res = await fetch(`${baseUrl}/api/voice/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: DEFAULT_VOICE }),
      })

      if (!res.ok) throw new Error('TTS failed')
      
      // We don't await play() to finish because it's a long stream
      await play(res)
      // updateState(VOICE_STATE.SPEAKING) happens in useEffect for isPlaying
    } catch (err) {
      console.error('[VoiceButton] Synthesize error:', err)
      updateState(VOICE_STATE.IDLE)
    }
  }

  const handleClick = () => {
    if (!consentShown) return // Block interaction until consent is handled
    setTranscribeError(null)

    if (!serverVoiceEnabled) {
      setServerVoiceErrorVisible(true)
      return
    }

    if (internalState === VOICE_STATE.IDLE) {
      // Start a voice conversation session
      setVoiceSessionActive(true)
      startRecording()
      updateState(VOICE_STATE.LISTENING)
    } else if (internalState === VOICE_STATE.LISTENING) {
      stopRecording()
      // handleTranscribe will be triggered by audioBlob effect
    } else if (internalState === VOICE_STATE.SPEAKING) {
      interruptAudio()
      updateState(VOICE_STATE.IDLE)
    } else if (internalState === VOICE_STATE.PROCESSING) {
      // User wants to cancel while waiting for response
      setAwaitingResponse(false)
      setVoiceSessionActive(false)
      updateState(VOICE_STATE.IDLE)
    }
  }

  // End voice session when user manually stops (non-hands-free)
  const endVoiceSession = useCallback(() => {
    setVoiceSessionActive(false)
    setAwaitingResponse(false)
  }, [])

  const handleConsentAllow = () => {
    localStorage.setItem(VOICE_CONSENT_KEY, 'true')
    setConsentShown(true)
  }

  const handleConsentSkip = () => {
    setConsentShown(true) // Just hide it for this session if skipped? Or keep hidden.
  }

  if (micDenied) {
    return (
      <div className="voice-denied-strip">
        <span>{t('voiceMicDenied')}</span>
        <a onClick={() => setMicDenied(false)}>{t('voiceRetry')}</a>
      </div>
    )
  }

  if (serverVoiceErrorVisible) {
    return (
      <div className="voice-denied-strip">
        <span>{t('voiceNotConfigured')}</span>
        <a onClick={() => setServerVoiceErrorVisible(false)}>{t('feedbackClose')}</a>
      </div>
    )
  }

  if (transcribeError) {
    return (
      <div className="voice-denied-strip">
        <span>{t('voiceUnavailable') || 'Voice feature is currently unavailable. Please try again later.'}</span>
        <a onClick={() => setTranscribeError(null)}>{t('feedbackClose')}</a>
      </div>
    )
  }

  return (
    <>
      <div className="voice-btn-group">
        <button 
          className="voice-btn" 
          onClick={handleClick}
          disabled={disabledProp}
          data-state={internalState}
          aria-label={internalState === VOICE_STATE.IDLE ? 'Start voice' : 'Stop'}
        >
          {internalState === VOICE_STATE.IDLE && (
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          )}
          {internalState === VOICE_STATE.LISTENING && (
            <div className="voice-btn__stop-square" style={{ width: 12, height: 12, background: 'currentColor', borderRadius: 2 }} />
          )}
          {internalState === VOICE_STATE.PROCESSING && (
            <div className="voice-btn__spinner" />
          )}
          {internalState === VOICE_STATE.SPEAKING && (
            <div className="voice-wave">
              <span/><span/><span/><span/>
            </div>
          )}
        </button>

        <button 
          className={`voice-mode-toggle ${handsFree ? 'active' : ''}`}
          onClick={() => {
            const newHandsFree = !handsFree
            setHandsFree(newHandsFree)
            // If turning off hands-free while in a session, end the session
            if (!newHandsFree && voiceSessionActive && internalState === VOICE_STATE.IDLE) {
              setVoiceSessionActive(false)
            }
          }}
          title={handsFree ? 'Hands-free: conversation continues automatically' : 'Push-to-talk: manual control'}
        >
          {handsFree ? 'HF' : 'PTT'}
        </button>
        {voiceSessionActive && handsFree && internalState === VOICE_STATE.IDLE && (
          <button 
            className="voice-end-session"
            onClick={() => {
              setVoiceSessionActive(false)
              setAwaitingResponse(false)
            }}
            title="End voice conversation"
          >
            ✕
          </button>
        )}
      </div>

      {!consentShown && (
        <div className="voice-consent-backdrop">
          <div className="voice-consent-modal">
            <h2>{t('voiceConsentTitle')}</h2>
            <p>{t('voiceConsentText')}</p>
            <div className="voice-consent-modal__actions">
              <button className="voice-consent-modal__skip" onClick={handleConsentSkip}>{t('voiceConsentLater')}</button>
              <button className="voice-consent-modal__allow" onClick={handleConsentAllow}>{t('voiceConsentAllow')}</button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
