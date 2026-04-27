import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Switch, Alert, ActivityIndicator, SafeAreaView,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme, THEMES } from '../../contexts/ThemeContext';
import { useTranslation, SUPPORTED_UI_LANGUAGES } from '../../contexts/TranslationContext';
import { apiBase, authHeaders, LANGUAGE_OPTIONS } from '../../lib/api';

interface Memory {
  id: number;
  fact_type: string;
  content: string;
}

export default function SettingsScreen() {
  const { token, user, signOut, refreshUser } = useAuth();
  const { theme, setThemeId, themes } = useTheme();
  const { t, uiLanguage, changeUiLanguage } = useTranslation();

  const [language, setLanguage] = useState(user?.preferred_language || 'en');
  const [birthYear, setBirthYear] = useState(user?.birth_year ? String(user.birth_year) : '');
  const [memoryEnabled, setMemoryEnabled] = useState(user?.memory_enabled ?? true);
  const [retentionDays, setRetentionDays] = useState(user?.memory_retention_days ?? 90);
  const [saving, setSaving] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [memoriesOpen, setMemoriesOpen] = useState(false);
  const [memoriesLoading, setMemoriesLoading] = useState(false);

  const base = apiBase();
  const s = makeStyles(theme);

  useEffect(() => {
    if (!user) return;
    if (user.preferred_language) setLanguage(user.preferred_language);
    if (user.birth_year) setBirthYear(String(user.birth_year));
    if (typeof user.memory_enabled === 'boolean') setMemoryEnabled(user.memory_enabled);
    if (user.memory_retention_days) setRetentionDays(user.memory_retention_days);
  }, [user]);

  const handleSave = async () => {
    const y = parseInt(birthYear, 10);
    const nowY = new Date().getFullYear();
    if (!Number.isFinite(y) || y < 1900 || y > nowY) {
      Alert.alert('Invalid year', `Enter a year between 1900 and ${nowY}.`);
      return;
    }
    setSaving(true);
    try {
      const r = await fetch(`${base}/api/auth/me`, {
        method: 'PATCH',
        headers: authHeaders(token || undefined),
        body: JSON.stringify({ preferred_language: language, birth_year: y, memory_enabled: memoryEnabled, memory_retention_days: retentionDays }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || 'Save failed');
      await refreshUser();
      Alert.alert('Saved', 'Your preferences have been updated.');
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not save');
    } finally {
      setSaving(false);
    }
  };

  const loadMemories = async () => {
    setMemoriesLoading(true);
    try {
      const r = await fetch(`${base}/api/memory`, { headers: authHeaders(token || undefined) });
      const d = await r.json();
      setMemories(d.memories || []);
    } catch { /* ignore */ }
    finally { setMemoriesLoading(false); }
  };

  const deleteMemory = async (id: number) => {
    try {
      await fetch(`${base}/api/memory/${id}`, { method: 'DELETE', headers: authHeaders(token || undefined) });
      setMemories(prev => prev.filter(m => m.id !== id));
    } catch { /* ignore */ }
  };

  const clearAllMemories = () => {
    Alert.alert('Clear all memories?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Clear', style: 'destructive', onPress: async () => {
          await fetch(`${base}/api/memory/clear`, { method: 'POST', headers: authHeaders(token || undefined) });
          setMemories([]);
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={s.container}>
      <ScrollView contentContainerStyle={s.scroll}>
        <Text style={s.pageTitle}>{t('settings')}</Text>

        {/* Response language */}
        <Text style={s.sectionLabel}>Response Language</Text>
        <View style={s.pickerWrap}>
          <Picker selectedValue={language} onValueChange={setLanguage} style={s.picker} dropdownIconColor={theme.colors.textMuted}>
            {LANGUAGE_OPTIONS.map(o => <Picker.Item key={o.code} label={o.label} value={o.code} color={theme.colors.text} />)}
          </Picker>
        </View>

        {/* UI language */}
        <Text style={s.sectionLabel}>Interface Language</Text>
        <View style={s.pickerWrap}>
          <Picker selectedValue={uiLanguage} onValueChange={changeUiLanguage} style={s.picker} dropdownIconColor={theme.colors.textMuted}>
            {SUPPORTED_UI_LANGUAGES.map(l => <Picker.Item key={l.code} label={l.label} value={l.code} color={theme.colors.text} />)}
          </Picker>
        </View>

        {/* Birth year */}
        <Text style={s.sectionLabel}>Year of Birth</Text>
        <Text style={s.hint}>Response style (child/teen/adult) is derived from your age.</Text>
        <View style={s.pickerWrap}>
          <Picker
            selectedValue={birthYear}
            onValueChange={setBirthYear}
            style={s.picker}
            dropdownIconColor={theme.colors.textMuted}
          >
            {Array.from({ length: new Date().getFullYear() - 1899 }, (_, i) => {
              const yr = String(new Date().getFullYear() - i);
              return <Picker.Item key={yr} label={yr} value={yr} color={theme.colors.text} />;
            })}
          </Picker>
        </View>

        {/* Theme */}
        <Text style={s.sectionLabel}>Theme</Text>
        <View style={s.themeRow}>
          {themes.map(th => (
            <TouchableOpacity
              key={th.id}
              style={[s.themeChip, { backgroundColor: th.colors.primary }, theme.id === th.id && s.themeChipActive]}
              onPress={() => setThemeId(th.id)}
            >
              <Text style={[s.themeChipText, { color: th.colors.primaryText }]}>{th.label.split(' ')[0]}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Memory */}
        <Text style={s.sectionLabel}>Conversation Memory</Text>
        <Text style={s.hint}>When enabled, facts from Guidance mode may be saved to personalise future chats.</Text>
        <View style={s.switchRow}>
          <Text style={s.switchLabel}>{t('memoryEnabled')}</Text>
          <Switch value={memoryEnabled} onValueChange={setMemoryEnabled} trackColor={{ true: theme.colors.primary }} />
        </View>
        <Text style={s.sectionLabel}>Keep memories for</Text>
        <View style={s.retentionRow}>
          {[30, 90, 180, 365].map(n => (
            <TouchableOpacity
              key={n}
              style={[s.retentionChip, retentionDays === n && s.retentionChipActive]}
              onPress={() => setRetentionDays(n)}
            >
              <Text style={[s.retentionText, retentionDays === n && s.retentionTextActive]}>{n}d</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Memory management */}
        <TouchableOpacity style={s.secondaryBtn} onPress={async () => { setMemoriesOpen(!memoriesOpen); if (!memoriesOpen && memories.length === 0) await loadMemories(); }}>
          <Text style={s.secondaryBtnText}>{memoriesOpen ? t('hideMemories') : t('viewMemories')}</Text>
        </TouchableOpacity>
        {memoriesOpen && (
          <View style={s.memoriesList}>
            {memoriesLoading ? <ActivityIndicator color={theme.colors.primary} /> :
              memories.length === 0 ? <Text style={s.emptyText}>{t('noMemoriesYet')}</Text> :
                memories.map(m => (
                  <View key={m.id} style={s.memoryItem}>
                    <Text style={s.memoryType}>{m.fact_type}</Text>
                    <Text style={s.memoryContent}>{m.content}</Text>
                    <TouchableOpacity onPress={() => deleteMemory(m.id)}>
                      <Text style={s.memoryDelete}>{t('removeMemory')}</Text>
                    </TouchableOpacity>
                  </View>
                ))
            }
            {memories.length > 0 && (
              <TouchableOpacity style={s.dangerBtn} onPress={clearAllMemories}>
                <Text style={s.dangerBtnText}>{t('clearAllMemories')}</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Save */}
        <TouchableOpacity style={s.saveBtn} onPress={handleSave} disabled={saving}>
          {saving ? <ActivityIndicator color={theme.colors.primaryText} /> : <Text style={s.saveBtnText}>{t('savePreferences')}</Text>}
        </TouchableOpacity>

        {/* Sign out */}
        <TouchableOpacity style={s.secondaryBtn} onPress={() => Alert.alert('Sign out?', '', [{ text: 'Cancel', style: 'cancel' }, { text: 'Sign out', style: 'destructive', onPress: signOut }])}>
          <Text style={s.secondaryBtnText}>{t('signOut')}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    scroll: { padding: 20, paddingBottom: 60 },
    pageTitle: { fontSize: 26, fontWeight: '700', color: theme.colors.text, marginBottom: 24 },
    sectionLabel: { fontSize: 13, fontWeight: '700', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.6, marginTop: 20, marginBottom: 8 },
    hint: { fontSize: 13, color: theme.colors.textMuted, marginBottom: 10, lineHeight: 18 },
    pickerWrap: { backgroundColor: theme.colors.inputBg, borderRadius: 10, borderWidth: 1, borderColor: theme.colors.border, marginBottom: 4, overflow: 'hidden' },
    picker: { color: theme.colors.text, height: 50 },
    themeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
    themeChip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, minWidth: 80, alignItems: 'center' },
    themeChipActive: { borderWidth: 2, borderColor: theme.colors.text },
    themeChipText: { fontWeight: '700', fontSize: 13 },
    switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
    switchLabel: { fontSize: 15, color: theme.colors.text, flex: 1 },
    retentionRow: { flexDirection: 'row', gap: 8, marginBottom: 8 },
    retentionChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 16, backgroundColor: theme.colors.surfaceAlt, borderWidth: 1, borderColor: theme.colors.border },
    retentionChipActive: { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
    retentionText: { fontSize: 13, color: theme.colors.textMuted, fontWeight: '600' },
    retentionTextActive: { color: theme.colors.primaryText },
    memoriesList: { marginTop: 10, gap: 8 },
    memoryItem: { backgroundColor: theme.colors.surfaceAlt, borderRadius: 10, padding: 12, borderWidth: 1, borderColor: theme.colors.border },
    memoryType: { fontSize: 11, fontWeight: '700', color: theme.colors.primary, marginBottom: 4, textTransform: 'uppercase' },
    memoryContent: { fontSize: 14, color: theme.colors.text, marginBottom: 8 },
    memoryDelete: { fontSize: 13, color: '#e05050', fontWeight: '600' },
    emptyText: { color: theme.colors.textMuted, fontSize: 14, textAlign: 'center', paddingVertical: 12 },
    saveBtn: { backgroundColor: theme.colors.primary, borderRadius: 12, paddingVertical: 15, alignItems: 'center', marginTop: 28, shadowColor: theme.colors.primary, shadowOpacity: 0.35, shadowRadius: 10, shadowOffset: { width: 0, height: 4 } },
    saveBtnText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 16 },
    secondaryBtn: { borderWidth: 1, borderColor: theme.colors.border, borderRadius: 12, paddingVertical: 13, alignItems: 'center', marginTop: 12, backgroundColor: theme.colors.surfaceAlt },
    secondaryBtnText: { color: theme.colors.text, fontWeight: '600', fontSize: 15 },
    dangerBtn: { borderRadius: 12, paddingVertical: 12, alignItems: 'center', marginTop: 8, backgroundColor: '#3a1515' },
    dangerBtnText: { color: '#e05050', fontWeight: '700', fontSize: 14 },
  });
}
