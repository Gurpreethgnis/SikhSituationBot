'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { useRealtimeVoice } from './useRealtimeVoice'
import { useTranslation } from '../../contexts/TranslationContext'
import './VoiceMode.css'

/**
 * VoiceMode Component
 * 
 * Full-screen immersive voice conversation interface using OpenAI Realtime API.
 * Features:
 * - Animated orb that responds to conversation state
 * - Low-latency (~200ms) voice conversations
 * - Auto turn-taking with server-side VAD
 * 
 * Props:
 *   isOpen - boolean; whether the voice mode overlay is visible
 *   onClose - () => void; callback to close the overlay
 *   token - string; JWT auth token
 *   voice - string; preferred TTS voice
 *   onMessage - (role, text) => void; callback when a message is transcribed
 */
export default function VoiceMode({
  isOpen,
  onClose,
  token,
  voice = 'coral',
  onMessage
}) {
  const { t } = useTranslation()
  const [error, setError] = useState(null)
  const [userTranscript, setUserTranscript] = useState('')
  const [assistantTranscript, setAssistantTranscript] = useState('')

  const handleTranscript = useCallback((text) => {
    setUserTranscript(text)
    onMessage?.('user', text)
  }, [onMessage])

  const handleAssistantText = useCallback((text) => {
    setAssistantTranscript(text)
    onMessage?.('assistant', text)
  }, [onMessage])

  const handleError = useCallback((err) => {
    console.error('[VoiceMode] Error:', err)
    setError(typeof err === 'string' ? err : 'Connection error')
  }, [])

  const {
    state,
    isConnected,
    connect,
    disconnect,
    interrupt
  } = useRealtimeVoice({
    token,
    voice,
    onTranscript: handleTranscript,
    onAssistantText: handleAssistantText,
    onError: handleError
  })

  useEffect(() => {
    if (isOpen && token) {
      setError(null)
      setUserTranscript('')
      setAssistantTranscript('')
      connect()
    }
    
    return () => {
      if (isConnected) {
        disconnect()
      }
    }
  }, [isOpen, token])

  const handleClose = useCallback(() => {
    disconnect()
    onClose?.()
  }, [disconnect, onClose])

  const handleOrbClick = useCallback(() => {
    if (state === 'speaking') {
      interrupt()
    }
  }, [state, interrupt])

  if (!isOpen) return null

  const getStatusText = () => {
    switch (state) {
      case 'connecting':
        return t('voiceConnecting') || 'Connecting...'
      case 'listening':
        return t('voiceListening') || 'Listening...'
      case 'thinking':
        return t('voiceThinking') || 'Thinking...'
      case 'speaking':
        return t('voiceSpeaking') || 'Speaking...'
      default:
        return ''
    }
  }

  const getTranscriptDisplay = () => {
    if (state === 'speaking' && assistantTranscript) {
      return assistantTranscript
    }
    if ((state === 'listening' || state === 'thinking') && userTranscript) {
      return userTranscript
    }
    return ''
  }

  return (
    <div className="voice-mode-overlay" data-state={state}>
      <div className="voice-mode-backdrop" />
      
      <button 
        className="voice-mode-close"
        onClick={handleClose}
        aria-label="Close voice mode"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>

      <div className="voice-mode-content">
        <div 
          className={`voice-mode-orb orb-${state}`}
          onClick={handleOrbClick}
          role="button"
          aria-label={state === 'speaking' ? 'Click to interrupt' : 'Voice indicator'}
        >
          <div className="orb-inner" />
          <div className="orb-glow" />
          <div className="orb-ring orb-ring-1" />
          <div className="orb-ring orb-ring-2" />
          <div className="orb-ring orb-ring-3" />
        </div>

        <div className="voice-mode-status">
          {getStatusText()}
        </div>

        {error && (
          <div className="voice-mode-error">
            {error === 'mic_denied' 
              ? (t('voiceMicDenied') || 'Microphone access denied')
              : error
            }
          </div>
        )}

        <div className="voice-mode-transcript">
          {getTranscriptDisplay()}
        </div>

        <div className="voice-mode-hint">
          {state === 'speaking' 
            ? (t('voiceTapToInterrupt') || 'Tap orb to interrupt')
            : state === 'listening'
              ? (t('voiceJustSpeak') || 'Just speak naturally')
              : ''
          }
        </div>
      </div>
    </div>
  )
}
