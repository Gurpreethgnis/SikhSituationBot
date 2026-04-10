import React, { useEffect, useState } from 'react';
import {
  View, Text, FlatList, TextInput, TouchableOpacity,
  StyleSheet, ActivityIndicator, SafeAreaView, Linking,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useTranslation } from '../../contexts/TranslationContext';
import { apiBase } from '../../lib/api';

interface Shabad {
  id: number;
  shabad_id: string;
  gurmukhi: string;
  english_translation?: string;
  romanization?: string;
  source?: string;
  sttm_link?: string;
}

export default function ParmaansScreen() {
  const { theme } = useTheme();
  const { t } = useTranslation();

  const [query, setQuery] = useState('');
  const [shabads, setShabads] = useState<Shabad[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const base = apiBase();
  const s = makeStyles(theme);

  const handleSearch = async () => {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setSearched(true);
    try {
      const r = await fetch(`${base}/api/search?q=${encodeURIComponent(q)}&mode=auto&limit=20`);
      const d = await r.json();
      setShabads((d.results || []).map((m: any) => ({
        id: m.id || m.shabad_id,
        shabad_id: m.shabad_id,
        gurmukhi: m.gurmukhi,
        english_translation: m.translation || m.english_translation,
        romanization: m.romanization,
        source: m.source,
        sttm_link: m.sttm_link,
      })));
    } catch {
      setShabads([]);
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }: { item: Shabad }) => (
    <View style={s.card}>
      {item.source ? <Text style={s.source}>{item.source}</Text> : null}
      <Text style={[s.gurmukhi, { fontFamily: 'NotoSansGurmukhi' }]}>{item.gurmukhi}</Text>
      {item.english_translation ? (
        <Text style={s.translation}>{item.english_translation}</Text>
      ) : null}
      {item.romanization ? (
        <Text style={s.romanization}>{item.romanization}</Text>
      ) : null}
      {item.sttm_link ? (
        <TouchableOpacity onPress={() => Linking.openURL(item.sttm_link!)}>
          <Text style={s.sttmLink}>{t('viewOnSikhiToTheMax')}</Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );

  return (
    <SafeAreaView style={s.container}>
      <View style={s.header}>
        <Text style={s.title}>☬ {t('parmaanLibraryLink')}</Text>
      </View>

      <View style={s.searchRow}>
        <TextInput
          style={s.searchInput}
          value={query}
          onChangeText={setQuery}
          placeholder="Search Gurbani by theme, word, or line…"
          placeholderTextColor={theme.colors.textMuted}
          returnKeyType="search"
          onSubmitEditing={handleSearch}
        />
        <TouchableOpacity style={s.searchBtn} onPress={handleSearch} disabled={loading}>
          <Text style={s.searchBtnText}>{t('search')}</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={s.center}>
          <ActivityIndicator color={theme.colors.primary} size="large" />
          <Text style={s.loadingText}>{t('seekingWisdom')}</Text>
        </View>
      ) : (
        <FlatList
          data={shabads}
          keyExtractor={(item) => item.shabad_id}
          contentContainerStyle={s.list}
          renderItem={renderItem}
          ListEmptyComponent={
            searched ? (
              <View style={s.center}>
                <Text style={s.emptyText}>No results found. Try a different search.</Text>
              </View>
            ) : (
              <View style={s.center}>
                <Text style={s.emptyTitle}>Search the Gurbani Library</Text>
                <Text style={s.emptySubtitle}>Find verses by theme, first letters, or meaning.</Text>
              </View>
            )
          }
        />
      )}
    </SafeAreaView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    header: { paddingHorizontal: 18, paddingTop: 12, paddingBottom: 8 },
    title: { fontSize: 22, fontWeight: '700', color: theme.colors.text },
    searchRow: { flexDirection: 'row', paddingHorizontal: 14, paddingBottom: 12, gap: 8 },
    searchInput: {
      flex: 1,
      backgroundColor: theme.colors.inputBg,
      color: theme.colors.text,
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 12,
      paddingHorizontal: 14,
      paddingVertical: 11,
      fontSize: 15,
    },
    searchBtn: { backgroundColor: theme.colors.primary, borderRadius: 12, paddingHorizontal: 18, justifyContent: 'center' },
    searchBtnText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 15 },
    list: { padding: 14, gap: 12 },
    card: {
      backgroundColor: theme.colors.surface,
      borderRadius: 14,
      padding: 16,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    source: { fontSize: 11, color: theme.colors.primary, fontWeight: '700', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
    gurmukhi: { fontSize: 17, color: theme.colors.text, lineHeight: 26, marginBottom: 8 },
    translation: { fontSize: 14, color: theme.colors.text, lineHeight: 20, marginBottom: 6 },
    romanization: { fontSize: 13, color: theme.colors.textMuted, fontStyle: 'italic', marginBottom: 8 },
    sttmLink: { color: theme.colors.primary, fontSize: 13, fontWeight: '600' },
    center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
    loadingText: { color: theme.colors.textMuted, marginTop: 14, fontSize: 14, fontStyle: 'italic' },
    emptyTitle: { fontSize: 20, fontWeight: '700', color: theme.colors.text, textAlign: 'center', marginBottom: 10 },
    emptySubtitle: { fontSize: 14, color: theme.colors.textMuted, textAlign: 'center', lineHeight: 22 },
    emptyText: { fontSize: 15, color: theme.colors.textMuted, textAlign: 'center' },
  });
}
