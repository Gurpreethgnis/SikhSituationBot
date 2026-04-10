import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useTranslation } from '../../contexts/TranslationContext';
import { apiBase, authHeaders, ASK_TIMEOUT_MS, GuidanceMode, ParmaanDiscoveryType, ParmaanComposerAction } from '../../lib/api';
import ChatInput from '../../components/ChatInput';
import MessageBubble from '../../components/MessageBubble';
import GuidanceModePicker from '../../components/GuidanceModePicker';
import ParmaanControls from '../../components/ParmaanControls';
import DisambiguationList from '../../components/DisambiguationList';
import Sidebar from '../../components/Sidebar';
import FeedbackModal from '../../components/FeedbackModal';
import * as Clipboard from 'expo-clipboard';
import { Share } from 'react-native';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Message {
  role: 'user' | 'assistant';
  content: string;
  shabad?: { gurmukhi: string; english_translation: string; romanization?: string; sttm_link?: string; shabad_id?: string } | null;
  isQuestion?: boolean;
  isDisambiguation?: boolean;
  disambiguationCandidates?: any[];
  originalQuery?: string;
  guidanceMode?: string;
}

interface Chat {
  id: number;
  title: string;
  updated_at: string;
  created_at?: string;
}

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------
export default function ChatScreen() {
  const { token, user } = useAuth();
  const { theme } = useTheme();
  const { t } = useTranslation();

  const [messages, setMessages] = useState<Message[]>([]);
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [guidanceMode, setGuidanceMode] = useState<GuidanceMode>('guidance');
  const [language, setLanguage] = useState(user?.preferred_language || 'en');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [shabadCount, setShabadCount] = useState<number | null>(null);

  // Parmaan state
  const [parmaanDiscoveryType, setParmaanDiscoveryType] = useState<ParmaanDiscoveryType>('similar');
  const [parmaanShabadCount, setParmaanShabadCount] = useState(5);
  const [parmaanComposerAction, setParmaanComposerAction] = useState<ParmaanComposerAction>('ask');
  const [parmaanPillValue, setParmaanPillValue] = useState('');
  const [parmaanSearchResults, setParmaanSearchResults] = useState<any[]>([]);
  const [parmaanSearchLoading, setParmaanSearchLoading] = useState(false);
  const [parmaanLookupEmpty, setParmaanLookupEmpty] = useState(false);

  // Feedback
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackContent, setFeedbackContent] = useState('');

  const flatListRef = useRef<FlatList>(null);
  const base = apiBase();
  const s = makeStyles(theme);

  // ------------------------------------------------------------------
  // Shabad count polling
  // ------------------------------------------------------------------
  useEffect(() => {
    const fetchCount = async () => {
      try {
        const r = await fetch(`${base}/api/stats/knowledge`, { cache: 'no-store' } as any);
        if (!r.ok) return;
        const d = await r.json();
        if (typeof d.shabad_count === 'number') setShabadCount(d.shabad_count);
      } catch { /* ignore */ }
    };
    fetchCount();
    const id = setInterval(fetchCount, 45_000);
    return () => clearInterval(id);
  }, [base]);

  // ------------------------------------------------------------------
  // Load chats
  // ------------------------------------------------------------------
  const refreshChats = useCallback(async () => {
    if (!token) return;
    try {
      const r = await fetch(`${base}/api/chats`, { headers: authHeaders(token) });
      if (!r.ok) return;
      const d = await r.json();
      setChats(d.chats || []);
    } catch { /* ignore */ }
  }, [base, token]);

  useEffect(() => { if (token) refreshChats(); }, [token, refreshChats]);

  // ------------------------------------------------------------------
  // Chat actions
  // ------------------------------------------------------------------
  const handleNewChat = async () => {
    setSidebarOpen(false);
    setMessages([]);
    setSuggestions([]);
    if (!token) { setActiveChatId(null); return; }
    try {
      const r = await fetch(`${base}/api/chats`, {
        method: 'POST', headers: authHeaders(token),
        body: JSON.stringify({ title: 'New chat' }),
      });
      if (!r.ok) return;
      const d = await r.json();
      setActiveChatId(d.chat.id);
      await refreshChats();
    } catch { /* ignore */ }
  };

  const handleSelectChat = async (chat: Chat) => {
    setSidebarOpen(false);
    if (!token) return;
    try {
      const r = await fetch(`${base}/api/chats/${chat.id}`, { headers: authHeaders(token) });
      if (!r.ok) return;
      const d = await r.json();
      setActiveChatId(chat.id);
      setMessages((d.chat?.messages || []).map((m: any) => ({
        role: m.role, content: m.content,
        shabad: m.shabad ? { gurmukhi: m.shabad.gurmukhi, english_translation: m.shabad.english_translation, romanization: m.shabad.romanization, sttm_link: m.shabad.sttm_link } : null,
      })));
    } catch { /* ignore */ }
  };

  const handleDeleteChat = async (chatId: number) => {
    if (!token) return;
    try {
      await fetch(`${base}/api/chats/${chatId}`, { method: 'DELETE', headers: authHeaders(token) });
      setChats(prev => prev.filter(c => c.id !== chatId));
      if (activeChatId === chatId) { setActiveChatId(null); setMessages([]); }
    } catch { /* ignore */ }
  };

  // ------------------------------------------------------------------
  // Send message
  // ------------------------------------------------------------------
  const handleSend = async (query: string, options: { anchorShabadId?: string; parmaanOriginalQuery?: string } = {}) => {
    if (!token) { Alert.alert('Sign in required', 'Please sign in to send messages.'); return; }
    setLoading(true);
    setSuggestions([]);
    const userMsg: Message = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);

    const messageHistory = [...messages, userMsg].map(m => ({ role: m.role, content: m.content }));

    try {
      let chatId = activeChatId;
      if (!chatId) {
        const rc = await fetch(`${base}/api/chats`, {
          method: 'POST', headers: authHeaders(token),
          body: JSON.stringify({ title: 'New chat' }),
        });
        const dj = await rc.json().catch(() => ({}));
        if (rc.ok && dj.chat?.id) { chatId = dj.chat.id; setActiveChatId(chatId); await refreshChats(); }
      }

      const body: any = {
        query, language,
        message_history: messageHistory.slice(-20),
        guidance_mode: guidanceMode,
      };
      if (guidanceMode === 'parmaan') {
        body.parmaan_discovery_type = parmaanDiscoveryType;
        body.parmaan_shabad_count = parmaanShabadCount;
      }
      if (options.anchorShabadId) body.anchor_shabad_id = options.anchorShabadId;
      if (options.parmaanOriginalQuery) body.parmaan_original_query = options.parmaanOriginalQuery;
      if (chatId) body.chat_id = chatId;

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), ASK_TIMEOUT_MS);
      let response: Response;
      try {
        response = await fetch(`${base}/ask`, {
          method: 'POST', headers: authHeaders(token),
          body: JSON.stringify(body), signal: controller.signal,
        });
      } finally { clearTimeout(timeout); }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Error ${response.status}`);
      }

      const data = await response.json();
      let content: string = data.response || '';
      let extracted: string[] = [];

      if (content.includes('[SUGGESTIONS]')) {
        const parts = content.split('[SUGGESTIONS]');
        content = parts[0].trim();
        extracted = parts[1].trim().split('\n').map((s: string) => s.replace(/^- /, '').trim()).filter(Boolean);
      }

      const aiMsg: Message = {
        role: 'assistant', content,
        shabad: data.shabad,
        isQuestion: data.is_clarification === true,
        isDisambiguation: data.is_disambiguation === true,
        disambiguationCandidates: data.disambiguation_candidates || [],
        originalQuery: data.original_query || '',
        guidanceMode: data.guidance_mode,
      };
      setMessages(prev => [...prev, aiMsg]);
      setSuggestions(extracted);

      if (data.chat_title && chatId) {
        setChats(prev => prev.map(c => c.id === chatId ? { ...c, title: data.chat_title } : c));
        await refreshChats();
      }
    } catch (err: any) {
      const aborted = err?.name === 'AbortError';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: aborted ? 'The request took too long. Please check your connection and try again.' : (err.message || 'Something went wrong.'),
      }]);
    } finally { setLoading(false); }
  };

  // ------------------------------------------------------------------
  // Parmaan search
  // ------------------------------------------------------------------
  const runParmaanSearch = async (rawQuery: string, mode: ParmaanComposerAction) => {
    const q = rawQuery.trim();
    if (!q || mode === 'ask') return;
    setParmaanSearchLoading(true);
    setParmaanLookupEmpty(false);
    try {
      let shabads: any[] = [];
      if (mode === 'theme') {
        const r = await fetch(`${base}/api/parmaans/search`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: q, limit: 15 }),
        });
        const d = await r.json();
        shabads = d.shabads || [];
      } else {
        const r = await fetch(`${base}/api/search?q=${encodeURIComponent(q)}&mode=auto&limit=15`);
        const d = await r.json();
        shabads = (d.results || []).map((m: any) => ({ shabad_id: m.shabad_id, gurmukhi: m.gurmukhi, english_translation: m.translation || m.english_translation }));
      }
      setParmaanSearchResults(shabads);
      setParmaanLookupEmpty(shabads.length === 0);
    } catch { setParmaanSearchResults([]); }
    finally { setParmaanSearchLoading(false); }
  };

  const handleParmaanPillSend = (text: string) => {
    if (parmaanComposerAction === 'ask') { handleSend(text); setParmaanPillValue(''); return; }
    runParmaanSearch(text, parmaanComposerAction);
  };

  const handleAnchorPick = (shabad: any, originalQuery?: string) => {
    const preview = (shabad.gurmukhi || shabad.english_translation || '').slice(0, 80);
    const label = preview ? `Selected: ${preview}` : `Selected shabad: ${shabad.shabad_id}`;
    handleSend(label, { anchorShabadId: shabad.shabad_id, parmaanOriginalQuery: originalQuery });
    setParmaanSearchResults([]);
    setParmaanPillValue('');
  };

  // ------------------------------------------------------------------
  // Share
  // ------------------------------------------------------------------
  const handleShare = async () => {
    if (!activeChatId || !token) { Alert.alert('Save the chat first', 'Send a message to create a chat you can share.'); return; }
    try {
      const r = await fetch(`${base}/api/chats/${activeChatId}/share`, { method: 'POST', headers: authHeaders(token) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      await Share.share({ message: `Check out this Gurbani guidance: ${d.url}`, url: d.url });
    } catch (err: any) { Alert.alert('Error', err.message || 'Could not create share link'); }
  };

  // ------------------------------------------------------------------
  // Empty state
  // ------------------------------------------------------------------
  const renderEmpty = () => (
    <View style={s.emptyState}>
      <Text style={s.khandaLarge}>☬</Text>
      <Text style={s.emptyTitle}>{t('appName')}</Text>
      <Text style={s.emptySubtitle}>{t('tagline')}</Text>
      {shabadCount != null && (
        <Text style={s.shabadCount}>{t('knowledgeShabadCount').replace('{count}', shabadCount.toLocaleString())}</Text>
      )}
    </View>
  );

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  return (
    <SafeAreaView style={s.container}>
      {/* Sidebar drawer */}
      <Sidebar
        isOpen={sidebarOpen}
        chats={chats}
        activeChatId={activeChatId}
        onClose={() => setSidebarOpen(false)}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        user={user}
      />

      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => setSidebarOpen(true)} style={s.headerBtn}>
          <Ionicons name="menu-outline" size={26} color={theme.colors.text} />
        </TouchableOpacity>
        <View style={s.headerCenter}>
          <Text style={s.headerTitle}>
            {guidanceMode === 'guidance' ? `📖 ${t('guidanceMode')}` : `🔍 ${t('parmaanMode')}`}
          </Text>
        </View>
        <TouchableOpacity onPress={handleShare} style={s.headerBtn} disabled={!activeChatId}>
          <Ionicons name="share-outline" size={24} color={activeChatId ? theme.colors.text : theme.colors.textMuted} />
        </TouchableOpacity>
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        ListEmptyComponent={renderEmpty}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        contentContainerStyle={messages.length === 0 ? { flex: 1 } : { paddingBottom: 12 }}
        renderItem={({ item, index }) => (
          <MessageBubble
            message={item}
            onFeedback={(content) => { setFeedbackContent(content); setFeedbackOpen(true); }}
            onDisambiguationSelect={handleAnchorPick}
          />
        )}
        ListFooterComponent={
          loading ? (
            <View style={s.loadingRow}>
              <ActivityIndicator color={theme.colors.primary} size="small" />
              <Text style={s.loadingText}>{t('seekingWisdom')}</Text>
            </View>
          ) : null
        }
      />

      {/* Suggestions */}
      {suggestions.length > 0 && !loading && (
        <FlatList
          horizontal
          data={suggestions.slice(0, 3)}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={s.suggestionsBar}
          style={s.suggestionsList}
          showsHorizontalScrollIndicator={false}
          renderItem={({ item }) => (
            <TouchableOpacity style={s.suggestionChip} onPress={() => handleSend(item)}>
              <Text style={s.suggestionText}>{item}</Text>
            </TouchableOpacity>
          )}
        />
      )}

      {/* Parmaan search results */}
      {guidanceMode === 'parmaan' && parmaanComposerAction !== 'ask' && parmaanSearchResults.length > 0 && (
        <DisambiguationList
          candidates={parmaanSearchResults}
          onSelect={(c) => handleAnchorPick(c, parmaanPillValue)}
          loading={parmaanSearchLoading}
        />
      )}

      {/* Input area */}
      <View style={s.footer}>
        {guidanceMode === 'parmaan' && (
          <ParmaanControls
            composerAction={parmaanComposerAction}
            onComposerActionChange={(a) => { setParmaanComposerAction(a); setParmaanSearchResults([]); }}
            discoveryType={parmaanDiscoveryType}
            onDiscoveryTypeChange={setParmaanDiscoveryType}
            shabadCount={parmaanShabadCount}
            onShabadCountChange={setParmaanShabadCount}
            disabled={loading}
          />
        )}
        <ChatInput
          onSend={guidanceMode === 'parmaan' ? handleParmaanPillSend : handleSend}
          disabled={loading}
          loading={loading}
          value={guidanceMode === 'parmaan' ? parmaanPillValue : undefined}
          onChange={guidanceMode === 'parmaan' ? (v) => { setParmaanPillValue(v); setParmaanLookupEmpty(false); } : undefined}
          placeholder={
            guidanceMode === 'parmaan'
              ? parmaanComposerAction === 'line' ? t('parmaanLinePlaceholder')
                : parmaanComposerAction === 'theme' ? t('parmaanThemePlaceholder')
                : t('parmaanMessagePlaceholder')
              : t('typeYourMessage')
          }
          leftSlot={
            <GuidanceModePicker mode={guidanceMode} onModeChange={(m) => { setGuidanceMode(m); setParmaanSearchResults([]); }} disabled={loading} />
          }
        />
      </View>

      <FeedbackModal
        visible={feedbackOpen}
        responseContent={feedbackContent}
        token={token}
        onClose={() => setFeedbackOpen(false)}
      />
    </SafeAreaView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    header: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
    headerBtn: { padding: 6, minWidth: 40, alignItems: 'center' },
    headerCenter: { flex: 1, alignItems: 'center' },
    headerTitle: { color: theme.colors.text, fontWeight: '600', fontSize: 15 },
    emptyState: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
    khandaLarge: { fontSize: 72, marginBottom: 16 },
    emptyTitle: { fontSize: 22, fontWeight: '700', color: theme.colors.text, marginBottom: 8 },
    emptySubtitle: { fontSize: 14, color: theme.colors.textMuted, textAlign: 'center', lineHeight: 22 },
    shabadCount: { marginTop: 16, fontSize: 12, color: theme.colors.textMuted },
    loadingRow: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 18, paddingVertical: 14 },
    loadingText: { color: theme.colors.textMuted, fontSize: 14, fontStyle: 'italic' },
    suggestionsBar: { paddingHorizontal: 14, paddingVertical: 8, gap: 8 },
    suggestionsList: { maxHeight: 52, flexGrow: 0 },
    suggestionChip: { backgroundColor: theme.colors.surfaceAlt, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 8, borderWidth: 1, borderColor: theme.colors.border },
    suggestionText: { color: theme.colors.text, fontSize: 13 },
    footer: { borderTopWidth: 1, borderTopColor: theme.colors.border, paddingHorizontal: 10, paddingBottom: 8, paddingTop: 6 },
  });
}
