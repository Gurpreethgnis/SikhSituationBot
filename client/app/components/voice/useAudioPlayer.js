'use client'

import { useCallback, useRef, useState } from 'react'
import { BARGE_IN_THRESHOLD } from './voiceConfig.js'

/**
 * useAudioPlayer
 *
 * Plays streaming TTS audio (audio/mpeg) via the Web Audio API.
 * Monitors mic volume via an AnalyserNode to detect barge-in (user speaking
 * while bot is playing), and fires onBargeIn() when detected.
 *
 * Returns:
 *   isPlaying     — boolean
 *   play(response, micStream?) — accepts a fetch Response w/ audio/mpeg body
 *   stop()        — pause playback and clean up
 *   interrupt()   — same as stop(); named explicitly for barge-in call sites
 */
export function useAudioPlayer() {
  const [isPlaying, setIsPlaying] = useState(false)

  const audioCtxRef = useRef(null)
  const sourceRef = useRef(null)
  const analyserRef = useRef(null)
  const bargeInRafRef = useRef(null)
  const onBargeInRef = useRef(null)

  // Ensure AudioContext exists and is resumed (browsers suspend on creation)
  const _getCtx = useCallback(() => {
    if (!audioCtxRef.current || audioCtxRef.current.state === 'closed') {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume().catch(() => {})
    }
    return audioCtxRef.current
  }, [])

  const _stopBargeInMonitor = useCallback(() => {
    if (bargeInRafRef.current) {
      cancelAnimationFrame(bargeInRafRef.current)
      bargeInRafRef.current = null
    }
  }, [])

  const stop = useCallback(() => {
    _stopBargeInMonitor()
    if (sourceRef.current) {
      try {
        sourceRef.current.stop()
        sourceRef.current.disconnect()
      } catch {
        /* already stopped */
      }
      sourceRef.current = null
    }
    setIsPlaying(false)
  }, [_stopBargeInMonitor])

  const interrupt = stop // semantic alias

  /**
   * Start monitoring mic volume via an AnalyserNode.
   * Calls onBargeIn() when RMS amplitude exceeds BARGE_IN_THRESHOLD.
   */
  const _startBargeInMonitor = useCallback(
    (micStream, onBargeIn) => {
      if (!micStream || !onBargeIn) return
      const ctx = _getCtx()
      try {
        const source = ctx.createMediaStreamSource(micStream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 512
        source.connect(analyser)
        analyserRef.current = analyser

        const buf = new Float32Array(analyser.fftSize)
        const check = () => {
          if (!analyserRef.current) return
          analyser.getFloatTimeDomainData(buf)
          let sumSq = 0
          for (let i = 0; i < buf.length; i++) sumSq += buf[i] * buf[i]
          const rms = Math.sqrt(sumSq / buf.length)
          if (rms > BARGE_IN_THRESHOLD) {
            onBargeIn()
            return // stop polling after triggering
          }
          bargeInRafRef.current = requestAnimationFrame(check)
        }
        bargeInRafRef.current = requestAnimationFrame(check)
      } catch (err) {
        console.warn('[useAudioPlayer] barge-in monitor failed:', err)
      }
    },
    [_getCtx]
  )

  /**
   * Play a streaming audio/mpeg fetch Response.
   *
   * @param {Response} response       — fetch Response with audio/mpeg body
   * @param {MediaStream} [micStream] — optional mic stream for barge-in detection
   * @param {Function} [onBargeIn]    — called when barge-in is detected
   */
  const play = useCallback(
    async (response, micStream, onBargeIn) => {
      if (!response || !response.ok) return
      onBargeInRef.current = onBargeIn || null

      try {
        const ctx = _getCtx()
        const arrayBuffer = await response.arrayBuffer()
        if (!arrayBuffer || arrayBuffer.byteLength === 0) return

        const audioBuffer = await ctx.decodeAudioData(arrayBuffer)
        const source = ctx.createBufferSource()
        source.buffer = audioBuffer
        source.connect(ctx.destination)

        source.onended = () => {
          setIsPlaying(false)
          _stopBargeInMonitor()
          sourceRef.current = null
          onBargeInRef.current?.(null) // signal natural end (null = no barge-in)
        }

        // Stop any previous playback before starting new one
        if (sourceRef.current) {
          try {
            sourceRef.current.stop()
            sourceRef.current.disconnect()
          } catch {
            /* already stopped */
          }
        }
        sourceRef.current = source
        source.start(0)
        setIsPlaying(true)

        // Start barge-in monitor if mic stream provided
        if (micStream && onBargeIn) {
          _startBargeInMonitor(micStream, onBargeIn)
        }
      } catch (err) {
        console.error('[useAudioPlayer] playback error:', err)
        setIsPlaying(false)
      }
    },
    [_getCtx, _stopBargeInMonitor, _startBargeInMonitor]
  )

  return { isPlaying, play, stop, interrupt }
}
