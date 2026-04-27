import { useState, useRef, useCallback, useEffect } from 'react';
import { Platform } from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { apiBase } from '../lib/api';

/**
 * useRealtimeVoice (Mobile)
 * 
 * Ported from web useRealtimeVoice.js for React Native / Expo.
 * Uses expo-av for audio recording and playback.
 */
export function useRealtimeVoice({
  token,
  voice = 'coral',
  onTranscript,
  onAssistantText,
  onError
}: {
  token: string | null;
  voice?: string;
  onTranscript?: (text: string) => void;
  onAssistantText?: (text: string) => void;
  onError?: (err: string) => void;
}) {
  const [state, setState] = useState<'idle' | 'connecting' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [isConnected, setIsConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);
  const playbackQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef(false);

  // Setup audio session for iOS handle silent mode etc.
  useEffect(() => {
    Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
      shouldDuckOthersIOS: true,
    }).catch(err => console.warn('Audio.setAudioModeAsync failed', err));

    return () => {
      cleanup();
    };
  }, []);

  const cleanup = useCallback(async () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (recordingRef.current) {
      await recordingRef.current.stopAndUnloadAsync().catch(() => {});
      recordingRef.current = null;
    }
    if (soundRef.current) {
      await soundRef.current.unloadAsync().catch(() => {});
      soundRef.current = null;
    }
    playbackQueueRef.current = [];
    isPlayingRef.current = false;
    setIsConnected(false);
    setState('idle');
  }, []);

  const processPlaybackQueue = useCallback(async () => {
    if (playbackQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      if (state === 'speaking') {
        setState('listening');
      }
      return;
    }

    isPlayingRef.current = true;
    const base64Audio = playbackQueueRef.current.shift();
    if (!base64Audio) return;

    try {
      // expo-av playback for streaming is tricky. 
      // For MVP, we save to a temp file and play it.
      // In production, a more robust PCM buffer player would be better.
      const tempFile = `${FileSystem.cacheDirectory}voice_chunk_${Date.now()}.wav`;
      // Note: This assumes the server sends a play-able format or we wrap it in a header.
      // OpenAI Realtime sends raw PCM16, which needs a WAV header to be played by expo-av easily.
      // Here we assume the server proxy might eventually wrap it or we do it here.
      // FOR NOW: This is a placeholder for the specialized PCM player.
      
      // await FileSystem.writeAsStringAsync(tempFile, base64Audio, { encoding: FileSystem.EncodingType.Base64 });
      // const { sound } = await Audio.Sound.createAsync({ uri: tempFile });
      // soundRef.current = sound;
      // await sound.playAsync();
      // sound.setOnPlaybackStatusUpdate((status) => {
      //   if (status.isLoaded && status.didJustFinish) {
      //     sound.unloadAsync();
      //     processPlaybackQueue();
      //   }
      // });
      
      // Mocking playback for now as real PCM16 -> expo-av is complex
      console.log('[VoiceMode] Playing audio delta...');
      setTimeout(() => processPlaybackQueue(), 500); // Simulate play time
      
    } catch (err) {
      console.error('[VoiceMode] Playback error', err);
      processPlaybackQueue();
    }
  }, [state]);

  const connect = useCallback(async () => {
    if (wsRef.current || !token) return;

    try {
      setState('connecting');
      
      // Request permissions
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        onError?.('Microphone permission denied');
        setState('idle');
        return;
      }

      // Resolve WS URL (simpler than web since we don't have window.location)
      const base = apiBase().replace(/^http/, 'ws');
      const url = `${base}/api/realtime/connect?token=${encodeURIComponent(token)}&voice=${encodeURIComponent(voice)}`;
      
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setState('listening');
        startRecording();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleServerMessage(data);
        } catch (err) {
          console.error('[VoiceMode] Parse error', err);
        }
      };

      ws.onerror = (err) => {
        console.error('[VoiceMode] WS error', err);
        onError?.('Connection error');
      };

      ws.onclose = () => {
        cleanup();
      };

    } catch (err) {
      console.error('[VoiceMode] Connection error', err);
      setState('idle');
    }
  }, [token, voice, onError]);

  const startRecording = async () => {
    try {
      // Recording settings for PCM16 24kHz (matching OpenAI)
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.pcm',
          outputFormat: 0, // RAW
          audioEncoder: 0, // DEFAULT
          sampleRate: 24000,
          numberOfChannels: 1,
          bitRate: 48000,
        },
        ios: {
          extension: '.pcm',
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 24000,
          numberOfChannels: 1,
          bitRate: 48000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {}
      });
      
      recordingRef.current = recording;
      await recording.startAsync();
      
      // Real-time chunking on mobile is hard without native modules.
      // One approach is to rotate files every 100ms or use a native PCM bridge.
      // FOR THE MOBILE MVP: We'll log that recording started.
      console.log('[VoiceMode] Recording started');
      
    } catch (err) {
      console.error('[VoiceMode] Recording error', err);
    }
  };

  const handleServerMessage = (data: any) => {
    switch (data.type) {
      case 'input_audio_buffer.speech_started':
        setState('listening');
        playbackQueueRef.current = [];
        isPlayingRef.current = false;
        break;
      case 'input_audio_buffer.speech_stopped':
        setState('thinking');
        break;
      case 'conversation.item.input_audio_transcription.completed':
        onTranscript?.(data.transcript);
        break;
      case 'response.audio.delta':
        if (data.delta) {
          if (state !== 'speaking') setState('speaking');
          playbackQueueRef.current.push(data.delta);
          if (!isPlayingRef.current) processPlaybackQueue();
        }
        break;
      case 'response.audio_transcript.done':
        onAssistantText?.(data.transcript);
        break;
      case 'response.done':
        if (!isPlayingRef.current) setState('listening');
        break;
      case 'error':
        onError?.(data.error?.message || 'Server error');
        break;
    }
  };

  const disconnect = useCallback(() => {
    cleanup();
  }, [cleanup]);

  const interrupt = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'response.cancel' }));
    }
    playbackQueueRef.current = [];
    isPlayingRef.current = false;
    setState('listening');
  }, []);

  return { state, isConnected, connect, disconnect, interrupt };
}
