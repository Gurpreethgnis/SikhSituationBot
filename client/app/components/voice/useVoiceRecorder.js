'use client'

import { useCallback, useRef, useState } from 'react'
import { MAX_RECORDING_MS } from './voiceConfig.js'

/**
 * useVoiceRecorder
 *
 * Abstracts getUserMedia → MediaRecorder → audio blob collection.
 *
 * Returns:
 *   isRecording  — boolean, true while mic is active
 *   startRecording() — request mic, begin collecting chunks
 *   stopRecording()  — stop MediaRecorder, finalize audioBlob
 *   audioBlob    — Blob | null, populated after stopRecording resolves
 *   error        — string | null, set on mic-denied or API failure (does NOT throw)
 *   clearBlob()  — reset audioBlob to null between turns
 */
export function useVoiceRecorder(options = {}) {
  const { vadEnabled = false, onSilence } = options
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [error, setError] = useState(null)

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const timeoutRef = useRef(null)
  const audioCtxRef = useRef(null)
  const analyserRef = useRef(null)
  const vadRafRef = useRef(null)

  const stopRecording = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (vadRafRef.current) {
      cancelAnimationFrame(vadRafRef.current)
      vadRafRef.current = null
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }

    const mr = mediaRecorderRef.current
    if (mr && mr.state !== 'inactive') {
      mr.stop()
    }
  }, [])

  const startRecording = useCallback(async () => {
    setError(null)
    setAudioBlob(null)
    chunksRef.current = []

    // --- Request microphone ---
    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('mic_denied')
      } else {
        setError(err.message || 'mic_unavailable')
      }
      return
    }

    // --- Optional VAD Setup ---
    if (vadEnabled) {
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext
        const ctx = new AudioContext()
        audioCtxRef.current = ctx
        const source = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 512
        source.connect(analyser)
        analyserRef.current = analyser

        const buffer = new Float32Array(analyser.fftSize)
        let lastSpeakTime = Date.now()
        const SILENCE_THRESHOLD = 0.015
        const SILENCE_TIMEOUT_MS = 1500

        const checkVoice = () => {
          if (!analyserRef.current) return
          analyser.getFloatTimeDomainData(buffer)
          let sumSq = 0
          for (let i = 0; i < buffer.length; i++) sumSq += buffer[i] * buffer[i]
          const rms = Math.sqrt(sumSq / buffer.length)

          const now = Date.now()
          if (rms > SILENCE_THRESHOLD) {
            lastSpeakTime = now
          }

          if (now - lastSpeakTime > SILENCE_TIMEOUT_MS) {
            onSilence?.()
            return // Stop loop
          }
          vadRafRef.current = requestAnimationFrame(checkVoice)
        }
        vadRafRef.current = requestAnimationFrame(checkVoice)
      } catch (err) {
        console.warn('[useVoiceRecorder] VAD setup failed:', err)
      }
    }

    // --- Pick MIME type (prefer webm/opus; Safari falls back to mp4) ---
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/mp4'

    let mr
    try {
      mr = new MediaRecorder(stream, { mimeType })
    } catch {
      mr = new MediaRecorder(stream)
    }

    mediaRecorderRef.current = mr

    mr.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
    }

    mr.onstop = () => {
      stream.getTracks().forEach((t) => t.stop())
      const blob = new Blob(chunksRef.current, { type: mr.mimeType || 'audio/webm' })
      setAudioBlob(blob)
      setIsRecording(false)
      mediaRecorderRef.current = null
    }

    mr.onerror = (e) => {
      setError(e.error?.message || 'recording_error')
      stream.getTracks().forEach((t) => t.stop())
      setIsRecording(false)
      mediaRecorderRef.current = null
    }

    mr.start(200)
    setIsRecording(true)

    timeoutRef.current = setTimeout(() => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
    }, MAX_RECORDING_MS)
  }, [vadEnabled, onSilence])

  const clearBlob = useCallback(() => setAudioBlob(null), [])

  return { isRecording, startRecording, stopRecording, audioBlob, error, clearBlob }
}
