import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, SafeAreaView, Alert, TextInput,
} from 'react-native';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useTranslation } from '../../contexts/TranslationContext';
import { apiBase, authHeaders } from '../../lib/api';

interface LLMSettings {
  model_id: string;
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
  
  // Notification form
  const [pushTitle, setPushTitle] = useState('Giani Ji');
  const [pushBody, setPushBody] = useState('');

  const base = apiBase();
  const s = makeStyles(theme);

  useEffect(() => {
    if (!token || !user?.is_admin) return;
    loadAdminData();
  }, [token]);

  const loadAdminData = async () => {
    try {
      const [sR, stR] = await Promise.all([
        fetch(`${base}/api/admin/llm-settings`, { headers: authHeaders(token || undefined) }),
        fetch(`${base}/stats/knowledge`),
      ]);
      if (sR.ok) { 
        const d = await sR.json(); 
        setSettings(d.settings || d); 
      }
      if (stR.ok) { 
        const d = await stR.json(); 
        setStats(d); 
      }
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const handleUpdateSettings = async (updates: Partial<LLMSettings>) => {
    if (!settings || !token) return;
    setSaving(true);
    try {
      const r = await fetch(`${base}/api/admin/llm-settings`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...settings, ...updates }),
      });
      if (r.ok) {
        setSettings({ ...settings, ...updates });
        Alert.alert('Success', 'Admin settings updated');
      }
    } catch {
      Alert.alert('Error', 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  const sendTestPush = async () => {
    if (!pushBody || !token) return;
    setSaving(true);
    try {
      const r = await fetch(`${base}/api/admin/push-single`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: pushTitle, body: pushBody, user_id: user?.id }),
      });
      if (r.ok) {
        Alert.alert('Sent', 'Test push notification sent to your device');
        setPushBody('');
      } else {
        const d = await r.json();
        Alert.alert('Error', d.error || 'Push failed');
      }
    } catch {
       Alert.alert('Error', 'Network error');
    } finally {
      setSaving(false);
    }
  };

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
        <View style={s.headerRow}>
          <Text style={s.pageTitle}>⚙️ Admin Panel</Text>
          {saving && <ActivityIndicator size="small" color={theme.colors.primary} />}
        </View>

        {/* Knowledge base stats */}
        <Text style={s.sectionLabel}>Knowledge Base</Text>
        <View style={s.statCard}>
          <Text style={s.statValue}>{stats?.shabad_count?.toLocaleString() ?? '—'}</Text>
          <Text style={s.statLabel}>Shabads indexed</Text>
        </View>

        {/* LLM Settings */}
        {settings && (
          <>
            <Text style={s.sectionLabel}>LLM Retrieval Counts</Text>
            <View style={s.card}>
              <View style={s.editRow}>
                <Text style={s.fieldLabel}>Guidance context size</Text>
                <View style={s.stepper}>
                  <TouchableOpacity onPress={() => handleUpdateSettings({ guidance_shabad_count: Math.max(1, settings.guidance_shabad_count - 1) })} style={s.stepBtn}>
                    <Text style={s.stepText}>-</Text>
                  </TouchableOpacity>
                  <Text style={s.stepVal}>{settings.guidance_shabad_count}</Text>
                  <TouchableOpacity onPress={() => handleUpdateSettings({ guidance_shabad_count: Math.min(10, settings.guidance_shabad_count + 1) })} style={s.stepBtn}>
                    <Text style={s.stepText}>+</Text>
                  </TouchableOpacity>
                </View>
              </View>

              <View style={[s.editRow, { marginTop: 16 }]}>
                <Text style={s.fieldLabel}>Parmaan results limit</Text>
                <View style={s.stepper}>
                  <TouchableOpacity onPress={() => handleUpdateSettings({ parmaan_shabad_count: Math.max(1, settings.parmaan_shabad_count - 1) })} style={s.stepBtn}>
                    <Text style={s.stepText}>-</Text>
                  </TouchableOpacity>
                  <Text style={s.stepVal}>{settings.parmaan_shabad_count}</Text>
                  <TouchableOpacity onPress={() => handleUpdateSettings({ parmaan_shabad_count: Math.min(20, settings.parmaan_shabad_count + 1) })} style={s.stepBtn}>
                    <Text style={s.stepText}>+</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </>
        )}

        {/* Push Notification Testing */}
        <Text style={s.sectionLabel}>Push Notifications</Text>
        <View style={s.card}>
          <Text style={s.fieldLabel}>Send test push to self</Text>
          <TextInput
            style={s.input}
            placeholder="Notification Body..."
            placeholderTextColor={theme.colors.textMuted}
            value={pushBody}
            onChangeText={setPushBody}
            multiline
          />
          <TouchableOpacity 
            style={[s.btn, { backgroundColor: theme.colors.primary }, !pushBody && { opacity: 0.5 }]} 
            onPress={sendTestPush}
            disabled={!pushBody || saving}
          >
            <Text style={s.btnText}>Send Test Push</Text>
          </TouchableOpacity>
        </View>

        <Text style={s.hint}>Full administrative tools and analytics available on the web portal.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    scroll: { padding: 20, paddingBottom: 60 },
    headerRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 },
    pageTitle: { fontSize: 24, fontWeight: '700', color: theme.colors.text },
    sectionLabel: { fontSize: 12, fontWeight: '700', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.7, marginTop: 24, marginBottom: 12 },
    statCard: { backgroundColor: theme.colors.surface, borderRadius: 16, padding: 24, alignItems: 'center', borderWidth: 1, borderColor: theme.colors.border },
    statValue: { fontSize: 36, fontWeight: '800', color: theme.colors.primary },
    statLabel: { fontSize: 13, color: theme.colors.textMuted, marginTop: 4 },
    card: { backgroundColor: theme.colors.surface, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: theme.colors.border },
    editRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    fieldLabel: { fontSize: 14, color: theme.colors.text, fontWeight: '600' },
    stepper: { flexDirection: 'row', alignItems: 'center', backgroundColor: theme.colors.surfaceAlt, borderRadius: 10, overflow: 'hidden', borderWidth: 1, borderColor: theme.colors.border },
    stepBtn: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.05)' },
    stepText: { fontSize: 20, color: theme.colors.text, fontWeight: '600' },
    stepVal: { width: 36, textAlign: 'center', color: theme.colors.text, fontWeight: '700' },
    input: { backgroundColor: theme.colors.surfaceAlt, borderRadius: 10, padding: 12, color: theme.colors.text, fontSize: 15, marginVertical: 12, minHeight: 60, textAlignVertical: 'top', borderWidth: 1, borderColor: theme.colors.border },
    btn: { paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
    btnText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 15 },
    hint: { fontSize: 12, color: theme.colors.textMuted, marginTop: 24, fontStyle: 'italic', textAlign: 'center' },
  });
}
