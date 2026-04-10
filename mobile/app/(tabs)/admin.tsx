import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, SafeAreaView, Alert, Switch,
} from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useTranslation } from '../../contexts/TranslationContext';
import { apiBase, authHeaders } from '../../lib/api';

interface LLMSettings {
  model: string;
  guidance_shabad_count: number;
  parmaan_shabad_count: number;
}

export default function AdminScreen() {
  const { token, user } = useAuth();
  const { theme } = useTheme();
  const { t } = useTranslation();
  const [settings, setSettings] = useState<LLMSettings | null>(null);
  const [stats, setStats] = useState<{ shabad_count?: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const base = apiBase();
  const s = makeStyles(theme);

  useEffect(() => {
    if (!token || !user?.is_admin) return;
    (async () => {
      try {
        const [sR, stR] = await Promise.all([
          fetch(`${base}/api/admin/llm-settings`, { headers: authHeaders(token) }),
          fetch(`${base}/api/stats/knowledge`),
        ]);
        if (sR.ok) { const d = await sR.json(); setSettings(d.settings || d); }
        if (stR.ok) { const d = await stR.json(); setStats(d); }
      } catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, [token]);

  if (!user?.is_admin) {
    return (
      <SafeAreaView style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ color: theme.colors.textMuted, fontSize: 16 }}>Admin access only</Text>
      </SafeAreaView>
    );
  }

  if (loading) {
    return (
      <SafeAreaView style={[s.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator color={theme.colors.primary} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.pageTitle}>⚙️ Admin Panel</Text>

        {/* Knowledge base stats */}
        <Text style={s.sectionLabel}>Knowledge Base</Text>
        <View style={s.statCard}>
          <Text style={s.statValue}>{stats?.shabad_count?.toLocaleString() ?? '—'}</Text>
          <Text style={s.statLabel}>Shabads indexed</Text>
        </View>

        {/* LLM Settings (read-only summary on mobile) */}
        {settings && (
          <>
            <Text style={s.sectionLabel}>LLM Settings</Text>
            <View style={s.card}>
              <Text style={s.cardRow}><Text style={s.bold}>Model:</Text> {settings.model}</Text>
              <Text style={s.cardRow}><Text style={s.bold}>Guidance shabads:</Text> {settings.guidance_shabad_count}</Text>
              <Text style={s.cardRow}><Text style={s.bold}>Parmaan shabads:</Text> {settings.parmaan_shabad_count}</Text>
            </View>
            <Text style={s.hint}>Full admin controls are available in the web app.</Text>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    scroll: { padding: 20, paddingBottom: 60 },
    pageTitle: { fontSize: 24, fontWeight: '700', color: theme.colors.text, marginBottom: 24 },
    sectionLabel: { fontSize: 12, fontWeight: '700', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.7, marginTop: 20, marginBottom: 10 },
    statCard: { backgroundColor: theme.colors.surface, borderRadius: 14, padding: 20, alignItems: 'center', borderWidth: 1, borderColor: theme.colors.border, marginBottom: 4 },
    statValue: { fontSize: 36, fontWeight: '800', color: theme.colors.primary },
    statLabel: { fontSize: 13, color: theme.colors.textMuted, marginTop: 4 },
    card: { backgroundColor: theme.colors.surface, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: theme.colors.border },
    cardRow: { fontSize: 14, color: theme.colors.text, paddingVertical: 5 },
    bold: { fontWeight: '700' },
    hint: { fontSize: 12, color: theme.colors.textMuted, marginTop: 10, fontStyle: 'italic' },
  });
}
