import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  SafeAreaView,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useTranslation } from '../contexts/TranslationContext';
import { useRealtimeVoice } from '../hooks/useRealtimeVoice';

interface VoiceModeProps {
  visible: boolean;
  onClose: () => void;
  token: string | null;
}

const { width, height } = Dimensions.get('window');

export default function VoiceMode({ visible, onClose, token }: VoiceModeProps) {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const [transcript, setTranscript] = useState('');
  const [assistantText, setAssistantText] = useState('');

  const { state, connect, disconnect, interrupt } = useRealtimeVoice({
    token,
    onTranscript: (txt) => {
      setTranscript(txt);
      setAssistantText('');
    },
    onAssistantText: (txt) => setAssistantText(txt),
    onError: (err) => console.error('[VoiceMode] Error:', err),
  });

  useEffect(() => {
    if (visible && token) {
      connect();
    } else {
      disconnect();
    }
  }, [visible, token]);

  const handleClose = () => {
    disconnect();
    onClose();
  };

  const statusText = () => {
    switch (state) {
      case 'connecting': return t('connecting');
      case 'listening': return t('listening');
      case 'thinking': return t('thinking');
      case 'speaking': return t('speaking');
      default: return '';
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={false}>
      <View style={[styles.container, { backgroundColor: '#0f0c1a' }]}>
        <SafeAreaView style={styles.safe}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={handleClose} style={styles.closeBtn}>
              <Ionicons name="close" size={28} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.title}>Giani Ji Voice Mode</Text>
            <View style={{ width: 44 }} />
          </View>

          {/* Content */}
          <View style={styles.content}>
            {/* Avatar / Visualizer placeholder */}
            <View style={styles.avatarContainer}>
              <View style={[styles.avatarGlow, { backgroundColor: theme.colors.primary, opacity: state === 'speaking' ? 0.4 : 0.2 }]} />
              <Text style={styles.avatarEmoji}>☬</Text>
            </View>

            <Text style={styles.status}>{statusText()}</Text>

            {/* Transcripts */}
            <View style={styles.transcriptWrap}>
              {transcript ? (
                <Text style={styles.userTranscript}>“{transcript}”</Text>
              ) : null}
              {assistantText ? (
                <Text style={styles.aiTranscript}>{assistantText}</Text>
              ) : state === 'speaking' ? (
                <Text style={styles.aiTranscript}>...</Text>
              ) : null}
            </View>
          </View>

          {/* Footer controls */}
          <View style={styles.footer}>
            <TouchableOpacity 
              style={[styles.bigMic, { backgroundColor: state === 'speaking' ? '#e05050' : theme.colors.primary }]}
              onPress={state === 'speaking' ? interrupt : undefined}
            >
              <Ionicons 
                name={state === 'speaking' ? "stop" : "mic"} 
                size={36} 
                color="#fff" 
              />
            </TouchableOpacity>
            <Text style={styles.hint}>
              {state === 'speaking' ? 'Tap to interrupt' : 'I\'m listening...'}
            </Text>
          </View>
        </SafeAreaView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  closeBtn: { padding: 8 },
  title: { color: '#fff', fontSize: 16, fontWeight: '600', opacity: 0.8 },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  avatarContainer: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: '#1a162d',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
    position: 'relative',
  },
  avatarGlow: {
    position: 'absolute',
    width: 200,
    height: 200,
    borderRadius: 100,
  },
  avatarEmoji: { fontSize: 64, color: '#fff' },
  status: { color: '#fff', fontSize: 18, fontWeight: '500', marginBottom: 40 },
  transcriptWrap: { width: '100%', alignItems: 'center' },
  userTranscript: { color: 'rgba(255,255,255,0.7)', fontSize: 16, fontStyle: 'italic', textAlign: 'center', marginBottom: 16 },
  aiTranscript: { color: '#fff', fontSize: 20, textAlign: 'center', lineHeight: 30 },
  footer: {
    paddingBottom: 40,
    alignItems: 'center',
  },
  bigMic: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    shadowOpacity: 0.3,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 4 },
    marginBottom: 16,
  },
  hint: { color: 'rgba(255,255,255,0.5)', fontSize: 14 },
});
