import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import Markdown from 'react-native-markdown-display';
import * as Clipboard from 'expo-clipboard';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useTranslation } from '../contexts/TranslationContext';

interface DisambiguationCandidate {
  shabad_id: string;
  gurmukhi?: string;
  romanization?: string;
  source?: string;
}

interface MessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    shabad?: { sttm_link?: string; gurmukhi?: string; english_translation?: string } | null;
    isDisambiguation?: boolean;
    disambiguationCandidates?: DisambiguationCandidate[];
    originalQuery?: string;
    guidanceMode?: string;
  };
  onFeedback?: (content: string) => void;
  onDisambiguationSelect?: (candidate: any, originalQuery?: string) => void;
  onSpeak?: (content: string) => void;
  speaking?: boolean;
}

export default function MessageBubble({ message, onFeedback, onDisambiguationSelect, onSpeak, speaking }: MessageProps) {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const isUser = message.role === 'user';
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await Clipboard.setStringAsync(message.content || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSttm = () => {
    if (message.shabad?.sttm_link) Linking.openURL(message.shabad.sttm_link);
  };

  const s = makeStyles(theme, isUser);

  const markdownStyles = {
    body: { color: isUser ? theme.colors.primaryText : theme.colors.text, fontSize: 16, lineHeight: 24 },
    heading1: { color: isUser ? theme.colors.primaryText : theme.colors.primary, fontWeight: '800' as const, fontSize: 20 },
    heading2: { color: isUser ? theme.colors.primaryText : theme.colors.text, fontWeight: '700' as const, fontSize: 18 },
    heading3: { color: isUser ? theme.colors.primaryText : theme.colors.text, fontWeight: '600' as const, fontSize: 16 },
    strong: { color: isUser ? theme.colors.primaryText : theme.colors.text, fontWeight: '800' as const },
    blockquote: { borderLeftColor: isUser ? theme.colors.primaryText : theme.colors.primary, borderLeftWidth: 4, paddingLeft: 12, opacity: 0.9, marginLeft: 0 },
    code_inline: { backgroundColor: isUser ? 'rgba(0,0,0,0.1)' : theme.colors.background, color: isUser ? theme.colors.primaryText : theme.colors.primary, fontFamily: 'monospace', paddingHorizontal: 4 } as any,
    fence: { backgroundColor: isUser ? 'rgba(0,0,0,0.1)' : theme.colors.background, borderRadius: 8, padding: 12, marginVertical: 8 } as any,
    // Gurmukhi class applied via custom rules below
  };

  return (
    <View style={s.wrapper}>
      <View style={s.toolbar}>
        <Text style={s.label}>{isUser ? t('you') : t('guru')}</Text>
        <View style={s.toolbarActions}>
          <TouchableOpacity onPress={handleCopy} style={s.actionBtn}>
            <Ionicons name={copied ? 'checkmark' : 'copy-outline'} size={14} color={theme.colors.textMuted} />
          </TouchableOpacity>
          {!isUser && message.content && !message.isDisambiguation && onSpeak && (
            <TouchableOpacity onPress={() => onSpeak(message.content)} style={s.actionBtn}>
              <Ionicons name={speaking ? "stop-circle-outline" : "volume-medium-outline"} size={16} color={speaking ? theme.colors.primary : theme.colors.textMuted} />
            </TouchableOpacity>
          )}
          {!isUser && message.content && !message.isDisambiguation && onFeedback && (
            <TouchableOpacity onPress={() => onFeedback(message.content)} style={s.actionBtn}>
              <Ionicons name="flag-outline" size={14} color={theme.colors.textMuted} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      <View style={s.bubble}>
        <Markdown style={markdownStyles}>{message.content}</Markdown>

        {/* Disambiguation candidates */}
        {message.isDisambiguation && (message.disambiguationCandidates || []).length > 0 && (
          <View style={s.disambigList}>
            {(message.disambiguationCandidates || []).map((c: DisambiguationCandidate, i: number) => (
              <TouchableOpacity
                key={`${c.shabad_id}-${i}`}
                style={s.disambigBtn}
                onPress={() => onDisambiguationSelect?.(c, message.originalQuery)}
              >
                {c.source ? <Text style={s.disambigMeta}>{c.source}</Text> : null}
                <Text style={[s.disambigGurmukhi, { fontFamily: 'NotoSansGurmukhi' }]} numberOfLines={2}>
                  {(c.gurmukhi || '').slice(0, 160)}
                </Text>
                {c.romanization ? (
                  <Text style={s.disambigRoman} numberOfLines={1}>{c.romanization.slice(0, 100)}</Text>
                ) : null}
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* STTM link */}
        {message.shabad?.sttm_link && message.guidanceMode !== 'parmaan' && !message.isDisambiguation && (
          <TouchableOpacity onPress={handleSttm} style={s.sttmLink}>
            <Text style={s.sttmText}>{t('viewOnSikhiToTheMax')}</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme'], isUser: boolean) {
  return StyleSheet.create({
    wrapper: { paddingHorizontal: 14, paddingVertical: 6 },
    toolbar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
    label: { fontSize: 11, fontWeight: '700', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 },
    toolbarActions: { flexDirection: 'row', gap: 6 },
    actionBtn: { padding: 4 },
    bubble: {
      backgroundColor: isUser ? theme.colors.primary : theme.colors.surfaceAlt,
      borderRadius: 18,
      borderWidth: 1,
      borderColor: theme.colors.border,
      padding: 16,
      elevation: 2,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
    },
    disambigList: { marginTop: 12, gap: 10 },
    disambigBtn: {
      backgroundColor: theme.colors.background,
      borderRadius: 12,
      padding: 14,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    disambigMeta: { fontSize: 11, color: theme.colors.primary, fontWeight: '700', marginBottom: 6, textTransform: 'uppercase' },
    disambigGurmukhi: { fontSize: 16, color: theme.colors.text, lineHeight: 24 },
    disambigRoman: { fontSize: 13, color: theme.colors.textMuted, marginTop: 6 },
    sttmLink: { marginTop: 12, alignSelf: 'flex-start' },
    sttmText: { color: isUser ? theme.colors.primaryText : theme.colors.primary, fontSize: 13, fontWeight: '700', textDecorationLine: 'underline' },
  });
}
