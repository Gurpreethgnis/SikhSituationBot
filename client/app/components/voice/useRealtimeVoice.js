'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * useRealtimeVoice
 *
 * Hook for real-time voice conversations using OpenAI's Realtime API
 * via a WebSocket proxy on the server.
 *
 * Features:
 * - Low-latency (~200ms) speech-to-speech conversations
 * - Server-side VAD (voice activity detection)
 * - Automatic turn-taking
 * - Audio streaming in both directions
 *
 * @param {Object} options
 * @param {string} options.token - JWT auth token
 * @param {string} options.voice - Voice preference (alloy, coral, etc.)
 * @param {string} options.wsUrl - WebSocket URL base (defaults to window.location)
 * @param {function} options.onTranscript - Called when user speech is transcribed
 * @param {function} options.onAssistantText - Called when assistant text is available
 * @param {function} options.onError - Called on errors
 */
export function useRealtimeVoice({
  token,
  voice = 'coral',
  wsUrl,
  onTranscript,
  onAssistantText,
  onError
} = {}) {
  const [state, setState] = useState('idle') // idle | connecting | listening | thinking | speaking
  const [isConnected, setIsConnected] = useState(false)
  
  const wsRef = useRef(null)
  const audioContextRef = useRef(null)
  const micStreamRef = useRef(null)
  const workletNodeRef = useRef(null)
  const playbackQueueRef = useRef([])
  const isPlayingRef = useRef(false)
  const nextPlayTimeRef = useRef(0)

  const getWsUrl = useCallback(() => {
    if (wsUrl) return wsUrl
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${proto}//${host}`
  }, [wsUrl])

  const initAudioContext = useCallback(async () => {
    if (audioContextRef.current) return audioContextRef.current
    
    const AudioContext = window.AudioContext || window.webkitAudioContext
    const ctx = new AudioContext({ sampleRate: 24000 })
    
    if (ctx.state === 'suspended') {
      await ctx.resume()
    }
    
    audioContextRef.current = ctx
    return ctx
  }, [])

  const startMicrophone = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 24000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      micStreamRef.current = stream
      const ctx = await initAudioContext()
      
      const source = ctx.createMediaStreamSource(stream)
      
      await ctx.audioWorklet.addModule('/audio-worklet-processor.js').catch(() => {
        console.warn('[RealtimeVoice] AudioWorklet not available, using ScriptProcessor fallback')
      })
      
      const bufferSize = 4096
      const scriptProcessor = ctx.createScriptProcessor(bufferSize, 1, 1)
      
      scriptProcessor.onaudioprocess = (e) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
        if (state !== 'listening') return
        
        const inputData = e.inputBuffer.getChannelData(0)
        const pcm16 = float32ToPcm16(inputData)
        const base64Audio = arrayBufferToBase64(pcm16.buffer)
        
        wsRef.current.send(JSON.stringify({
          type: 'input_audio_buffer.append',
          audio: base64Audio
        }))
      }
      
      source.connect(scriptProcessor)
      scriptProcessor.connect(ctx.destination)
      workletNodeRef.current = scriptProcessor
      
      return true
    } catch (err) {
      console.error('[RealtimeVoice] Microphone error:', err)
      onError?.('mic_denied')
      return false
    }
  }, [initAudioContext, state, onError])

  const stopMicrophone = useCallback(() => {
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect()
      workletNodeRef.current = null
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(track => track.stop())
      micStreamRef.current = null
    }
  }, [])

  const playAudioChunk = useCallback(async (base64Audio) => {
    const ctx = audioContextRef.current
    if (!ctx) return
    
    const pcm16 = base64ToPcm16(base64Audio)
    const float32 = pcm16ToFloat32(pcm16)
    
    const audioBuffer = ctx.createBuffer(1, float32.length, 24000)
    audioBuffer.getChannelData(0).set(float32)
    
    playbackQueueRef.current.push(audioBuffer)
    
    if (!isPlayingRef.current) {
      processPlaybackQueue()
    }
  }, [])

  const processPlaybackQueue = useCallback(() => {
    const ctx = audioContextRef.current
    if (!ctx || playbackQueueRef.current.length === 0) {
      isPlayingRef.current = false
      if (state === 'speaking') {
        setState('listening')
      }
      return
    }
    
    isPlayingRef.current = true
    const buffer = playbackQueueRef.current.shift()
    
    const source = ctx.createBufferSource()
    source.buffer = buffer
    source.connect(ctx.destination)
    
    const now = ctx.currentTime
    const startTime = Math.max(now, nextPlayTimeRef.current)
    nextPlayTimeRef.current = startTime + buffer.duration
    
    source.onended = () => {
      processPlaybackQueue()
    }
    
    source.start(startTime)
  }, [state])

  const clearPlaybackQueue = useCallback(() => {
    playbackQueueRef.current = []
    nextPlayTimeRef.current = 0
    isPlayingRef.current = false
  }, [])

  const connect = useCallback(async () => {
    if (wsRef.current) return
    if (!token) {
      onError?.('no_token')
      return
    }
    
    setState('connecting')
    
    const micStarted = await startMicrophone()
    if (!micStarted) {
      setState('idle')
      return
    }
    
    const base = getWsUrl()
    const url = `${base}/api/realtime/connect?token=${encodeURIComponent(token)}&voice=${encodeURIComponent(voice)}`
    
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws
      
      ws.onopen = () => {
        console.log('[RealtimeVoice] Connected')
        setIsConnected(true)
        setState('listening')
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleServerMessage(data)
        } catch (err) {
          console.error('[RealtimeVoice] Parse error:', err)
        }
      }
      
      ws.onerror = (err) => {
        console.error('[RealtimeVoice] WebSocket error:', err)
        onError?.('connection_error')
      }
      
      ws.onclose = (event) => {
        console.log('[RealtimeVoice] Disconnected:', event.code, event.reason)
        cleanup()
      }
      
    } catch (err) {
      console.error('[RealtimeVoice] Connection error:', err)
      onError?.('connection_error')
      setState('idle')
    }
  }, [token, voice, getWsUrl, startMicrophone, onError])

  const handleServerMessage = useCallback((data) => {
    const type = data.type
    
    switch (type) {
      case 'session.created':
      case 'session.updated':
        console.log('[RealtimeVoice] Session ready')
        break
        
      case 'input_audio_buffer.speech_started':
        setState('listening')
        clearPlaybackQueue()
        break
        
      case 'input_audio_buffer.speech_stopped':
        setState('thinking')
        break
        
      case 'conversation.item.input_audio_transcription.completed':
        onTranscript?.(data.transcript)
        break
        
      case 'response.audio.delta':
        if (data.delta) {
          if (state !== 'speaking') {
            setState('speaking')
          }
          playAudioChunk(data.delta)
        }
        break
        
      case 'response.audio.done':
        break
        
      case 'response.audio_transcript.delta':
        break
        
      case 'response.audio_transcript.done':
        onAssistantText?.(data.transcript)
        break
        
      case 'response.done':
        if (!isPlayingRef.current) {
          setState('listening')
        }
        break
        
      case 'error':
        const errorMsg = data.error?.message || 'Unknown error'
        console.error('[RealtimeVoice] Server error:', errorMsg)
        onError?.(errorMsg)
        break
        
      default:
        break
    }
  }, [state, onTranscript, onAssistantText, onError, playAudioChunk, clearPlaybackQueue])

  const disconnect = useCallback(() => {
    cleanup()
  }, [])

  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    stopMicrophone()
    clearPlaybackQueue()
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    setIsConnected(false)
    setState('idle')
  }, [stopMicrophone, clearPlaybackQueue])

  const interrupt = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'response.cancel' }))
    }
    clearPlaybackQueue()
    setState('listening')
  }, [clearPlaybackQueue])

  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  return {
    state,
    isConnected,
    connect,
    disconnect,
    interrupt
  }
}

function float32ToPcm16(float32Array) {
  const pcm16 = new Int16Array(float32Array.length)
  for (let i = 0; i < float32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Array[i]))
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return pcm16
}

function pcm16ToFloat32(pcm16Array) {
  const float32 = new Float32Array(pcm16Array.length)
  for (let i = 0; i < pcm16Array.length; i++) {
    float32[i] = pcm16Array[i] / (pcm16Array[i] < 0 ? 0x8000 : 0x7FFF)
  }
  return float32
}

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary)
}

function base64ToPcm16(base64) {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new Int16Array(bytes.buffer)
}
