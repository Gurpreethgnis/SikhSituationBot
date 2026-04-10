import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, StyleSheet, ActivityIndicator,
  TouchableOpacity, SafeAreaView,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Markdown from 'react-native-markdown-display';
import { apiBase } from '../../lib/api';
import { useTheme } from '../../contexts/ThemeContext';

interface SharedMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function SharedChatScreen() {
  const { shareId } = useLocalSearchParams<{ shareId: string }>();
  const { theme } = useTheme();
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [messages, setMessages] = useState<SharedMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const s = makeStyles(theme);

  useEffect(() => {
    if (!shareId) return;
    (async () => {
      try {
        const base = apiBase();
        const r = await fetch(`${base}/api/shared/${shareId}`);
        if (!r.ok) { setNotFound(true); return; }
        const d = await r.json();
        setTitle(d.chat?.title || 'Shared conversation');
        setMessages(d.chat?.messages || []);
      } catch { setNotFound(true); }
      finally { setLoading(false); }
    })();
  }, [shareId]);

  const markdownStyles = {
    body: { color: theme.colors.text, fontSize: 15, lineHeight: 22 },
    strong: { fontWeight: '700' as const, color: theme.colors.text },
    blockquote: { borderLeftColor: theme.colors.primary, borderLeftWidth: 3, paddingLeft: 12, opacity: 0.9, marginLeft: 0 },
  };

  if (loading) {
    return (
      <SafeAreaView style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator color={theme.colors.primary} size="large" />
        <Text style={s.loadingText}>Loading conversation…</Text>
      </SafeAreaView>
    );
  }

  if (notFound) {
    return (
      <SafeAreaView style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={s.emoji}>☬</Text>
        <Text style={s.notFoundTitle}>Not found</Text>
        <Text style={s.notFoundText}>This conversation is no longer shared or does not exist.</Text>
        <TouchableOpacity style={s.backBtn} onPress={() => router.back()}>
          <Text style={s.backBtnText}>Go back</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.headerBtn}>
          <Ionicons name="close" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <Text style={s.headerTitle} numberOfLines={1}>{title}</Text>
        <View style={s.headerBtn} />
      </View>

      <FlatList
        data={messages}
        keyExtractor={(_, i) => String(i)}
        contentContainerStyle={s.list}
        renderItem={({ item }) => (
          <View style={s.message}>
            <Text style={s.roleLabel}>{item.role === 'user' ? 'You' : 'Guru'}</Text>
            <View style={[s.bubble, { backgroundColor: item.role === 'user' ? theme.colors.userBubble : theme.colors.assistantBubble }]}>
              <Markdown style={markdownStyles}>{item.content}</Markdown>
            </View>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
    headerBtn: { width: 36 },
    headerTitle: { flex: 1, textAlign: 'center', fontSize: 16, fontWeight: '700', color: theme.colors.text },
    list: { padding: 14, gap: 14 },
    message: {},
    roleLabel: { fontSize: 11, fontWeight: '700', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 5 },
    bubble: { borderRadius: 14, padding: 14, borderWidth: 1, borderColor: theme.colors.border },
    loadingText: { color: theme.colors.textMuted, marginTop: 14, fontSize: 15 },
    emoji: { fontSize: 56, marginBottom: 16 },
    notFoundTitle: { fontSize: 22, fontWeight: '700', color: theme.colors.text, marginBottom: 10 },
    notFoundText: { fontSize: 15, color: theme.colors.textMuted, textAlign: 'center', lineHeight: 22, marginBottom: 24 },
    backBtn: { backgroundColor: theme.colors.primary, borderRadius: 12, paddingHorizontal: 32, paddingVertical: 13 },
    backBtnText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 15 },
  });
}
