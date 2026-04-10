import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useTranslation } from '../contexts/TranslationContext';
import type { ParmaanDiscoveryType, ParmaanComposerAction } from '../lib/api';

interface Props {
  composerAction: ParmaanComposerAction;
  onComposerActionChange: (a: ParmaanComposerAction) => void;
  discoveryType: ParmaanDiscoveryType;
  onDiscoveryTypeChange: (t: ParmaanDiscoveryType) => void;
  shabadCount: number;
  onShabadCountChange: (n: number) => void;
  disabled?: boolean;
}

const COMPOSER_ACTIONS: { key: ParmaanComposerAction; label: string }[] = [
  { key: 'ask', label: 'Ask' },
  { key: 'line', label: 'Find Line' },
  { key: 'theme', label: 'By Theme' },
];

const DISCOVERY_TYPES: { key: ParmaanDiscoveryType; labelKey: string }[] = [
  { key: 'similar', labelKey: 'parmaanDiscoverySimilar' },
  { key: 'topic', labelKey: 'parmaanDiscoveryTopic' },
  { key: 'dissimilar', labelKey: 'parmaanDiscoveryContrasts' },
];

export default function ParmaanControls({
  composerAction, onComposerActionChange,
  discoveryType, onDiscoveryTypeChange,
  shabadCount, onShabadCountChange,
  disabled,
}: Props) {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      {/* Composer action row */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.rowScroll} contentContainerStyle={s.rowContent}>
        {COMPOSER_ACTIONS.map((a) => (
          <TouchableOpacity
            key={a.key}
            style={[s.chip, composerAction === a.key && s.chipActive]}
            onPress={() => onComposerActionChange(a.key)}
            disabled={disabled}
          >
            <Text style={[s.chipText, composerAction === a.key && s.chipTextActive]}>{a.label}</Text>
          </TouchableOpacity>
        ))}
        <View style={s.divider} />
        {/* Discovery type — only relevant when composer is ask */}
        {composerAction === 'ask' && DISCOVERY_TYPES.map((d) => (
          <TouchableOpacity
            key={d.key}
            style={[s.chip, discoveryType === d.key && s.chipActive]}
            onPress={() => onDiscoveryTypeChange(d.key)}
            disabled={disabled}
          >
            <Text style={[s.chipText, discoveryType === d.key && s.chipTextActive]}>{t(d.labelKey as any)}</Text>
          </TouchableOpacity>
        ))}
        {/* Shabad count */}
        {composerAction === 'ask' && (
          <View style={s.countRow}>
            {[3, 5, 8].map((n) => (
              <TouchableOpacity
                key={n}
                style={[s.countBtn, shabadCount === n && s.chipActive]}
                onPress={() => onShabadCountChange(n)}
                disabled={disabled}
              >
                <Text style={[s.chipText, shabadCount === n && s.chipTextActive]}>{n}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { marginBottom: 6 },
    rowScroll: { flexGrow: 0 },
    rowContent: { flexDirection: 'row', gap: 6, paddingVertical: 4, paddingHorizontal: 2, alignItems: 'center' },
    chip: {
      borderRadius: 16,
      paddingHorizontal: 12,
      paddingVertical: 5,
      backgroundColor: theme.colors.surfaceAlt,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    chipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
    chipText: { fontSize: 12, color: theme.colors.textMuted, fontWeight: '600' },
    chipTextActive: { color: theme.colors.primaryText },
    divider: { width: 1, height: 20, backgroundColor: theme.colors.border, marginHorizontal: 4 },
    countRow: { flexDirection: 'row', gap: 4 },
    countBtn: {
      borderRadius: 14,
      paddingHorizontal: 9,
      paddingVertical: 5,
      backgroundColor: theme.colors.surfaceAlt,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
  });
}
