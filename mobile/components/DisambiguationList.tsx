import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';

interface Candidate {
  shabad_id: string;
  gurmukhi?: string;
  english_translation?: string;
  romanization?: string;
  source?: string;
}

interface Props {
  candidates: Candidate[];
  onSelect: (candidate: Candidate) => void;
  loading?: boolean;
}

export default function DisambiguationList({ candidates, onSelect, loading }: Props) {
  const { theme } = useTheme();
  const s = makeStyles(theme);

  if (loading) {
    return (
      <View style={s.loadingContainer}>
        <ActivityIndicator color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <View style={s.container}>
      <Text style={s.hint}>Select a verse to explore</Text>
      <FlatList
        data={candidates}
        keyExtractor={(item) => item.shabad_id}
        style={s.list}
        renderItem={({ item }) => (
          <TouchableOpacity style={s.item} onPress={() => onSelect(item)}>
            {item.source ? <Text style={s.source}>{item.source}</Text> : null}
            <Text style={[s.gurmukhi, { fontFamily: 'NotoSansGurmukhi' }]} numberOfLines={2}>
              {(item.gurmukhi || '').slice(0, 180)}
            </Text>
            {item.english_translation ? (
              <Text style={s.translation} numberOfLines={1}>{item.english_translation.slice(0, 100)}</Text>
            ) : null}
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { maxHeight: 260, borderTopWidth: 1, borderTopColor: theme.colors.border, backgroundColor: theme.colors.surface },
    hint: { padding: 10, fontSize: 12, color: theme.colors.textMuted, fontStyle: 'italic' },
    list: { flex: 1 },
    item: {
      padding: 12,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.border,
      backgroundColor: theme.colors.surfaceAlt,
      marginHorizontal: 10,
      marginBottom: 6,
      borderRadius: 10,
    },
    source: { fontSize: 11, color: theme.colors.primary, fontWeight: '700', marginBottom: 4 },
    gurmukhi: { fontSize: 15, color: theme.colors.text, lineHeight: 22 },
    translation: { fontSize: 12, color: theme.colors.textMuted, marginTop: 4, fontStyle: 'italic' },
    loadingContainer: { padding: 20, alignItems: 'center' },
  });
}
