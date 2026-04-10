import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { apiBase, authHeaders } from '../lib/api';

interface Props {
  visible: boolean;
  responseContent: string;
  token: string | null;
  onClose: () => void;
}

export default function FeedbackModal({ visible, responseContent, token, onClose }: Props) {
  const { theme } = useTheme();
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const s = makeStyles(theme);

  const handleSubmit = async () => {
    if (!description.trim()) { Alert.alert('Please describe the issue'); return; }
    if (!token) { Alert.alert('Sign in required'); return; }
    setLoading(true);
    try {
      const base = apiBase();
      const r = await fetch(`${base}/api/feedback`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify({
          description: description.trim().slice(0, 2000),
          response_snippet: responseContent.slice(0, 500),
          platform: 'mobile',
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || 'Submission failed');
      Alert.alert('Thank you!', 'Your feedback has been submitted.');
      setDescription('');
      onClose();
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not submit feedback');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="formSheet" onRequestClose={onClose}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={s.container}>
        <View style={s.header}>
          <Text style={s.title}>Submit Feedback</Text>
          <TouchableOpacity onPress={onClose} style={s.closeBtn}>
            <Text style={s.closeBtnText}>Cancel</Text>
          </TouchableOpacity>
        </View>
        <ScrollView style={s.body} keyboardShouldPersistTaps="handled">
          <Text style={s.label}>What was wrong with this response?</Text>
          <TextInput
            style={s.textarea}
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={5}
            placeholder="Describe the issue…"
            placeholderTextColor={theme.colors.textMuted}
            maxLength={2000}
          />
          <Text style={s.label}>Response snippet (auto-filled)</Text>
          <Text style={s.snippet} numberOfLines={4}>{responseContent.slice(0, 300)}</Text>
        </ScrollView>
        <View style={s.footer}>
          <TouchableOpacity style={s.submitBtn} onPress={handleSubmit} disabled={loading}>
            {loading ? <ActivityIndicator color={theme.colors.primaryText} /> : <Text style={s.submitText}>Submit Feedback</Text>}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 18, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
    title: { fontSize: 18, fontWeight: '700', color: theme.colors.text },
    closeBtn: { padding: 4 },
    closeBtnText: { color: theme.colors.primary, fontSize: 16 },
    body: { flex: 1, padding: 20 },
    label: { fontSize: 13, color: theme.colors.textMuted, fontWeight: '600', marginBottom: 8, marginTop: 16 },
    textarea: {
      backgroundColor: theme.colors.inputBg,
      color: theme.colors.text,
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 10,
      padding: 12,
      fontSize: 15,
      minHeight: 120,
      textAlignVertical: 'top',
    },
    snippet: { color: theme.colors.textMuted, fontSize: 13, fontStyle: 'italic', lineHeight: 20, padding: 10, backgroundColor: theme.colors.surfaceAlt, borderRadius: 8 },
    footer: { padding: 20, borderTopWidth: 1, borderTopColor: theme.colors.border },
    submitBtn: { backgroundColor: theme.colors.primary, borderRadius: 12, paddingVertical: 15, alignItems: 'center' },
    submitText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 16 },
  });
}
