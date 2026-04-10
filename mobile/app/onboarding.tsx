import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useTranslation } from '../contexts/TranslationContext';
import { apiBase, authHeaders } from '../lib/api';

export default function OnboardingScreen() {
  const { token, refreshUser } = useAuth();
  const { theme } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  const [birthYear, setBirthYear] = useState('');
  const [loading, setLoading] = useState(false);

  const s = makeStyles(theme);

  const handleContinue = async () => {
    const y = parseInt(birthYear, 10);
    const nowY = new Date().getFullYear();
    if (!Number.isFinite(y) || y < 1900 || y > nowY) {
      Alert.alert('Invalid year', `Please enter a year between 1900 and ${nowY}.`);
      return;
    }
    setLoading(true);
    try {
      const base = apiBase();
      const r = await fetch(`${base}/api/auth/me`, {
        method: 'PATCH',
        headers: authHeaders(token || undefined),
        body: JSON.stringify({ birth_year: y }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.error || 'Failed to save');
      await refreshUser();
      router.replace('/(tabs)/chat');
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Could not save birth year');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={s.container}>
      <View style={s.inner}>
        <Text style={s.emoji}>☬</Text>
        <Text style={s.title}>{t('onboardingTitle')}</Text>
        <Text style={s.subtitle}>{t('onboardingSubtitle')}</Text>

        <TextInput
          style={s.input}
          value={birthYear}
          onChangeText={setBirthYear}
          keyboardType="number-pad"
          placeholder={`e.g. ${new Date().getFullYear() - 30}`}
          placeholderTextColor={theme.colors.textMuted}
          maxLength={4}
        />

        <TouchableOpacity style={s.btn} onPress={handleContinue} disabled={loading}>
          {loading ? (
            <ActivityIndicator color={theme.colors.primaryText} />
          ) : (
            <Text style={s.btnText}>{t('onboardingContinue')}</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    inner: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
    emoji: { fontSize: 64, marginBottom: 24 },
    title: { fontSize: 24, fontWeight: '700', color: theme.colors.text, textAlign: 'center', marginBottom: 12 },
    subtitle: { fontSize: 15, color: theme.colors.textMuted, textAlign: 'center', lineHeight: 22, marginBottom: 32 },
    input: {
      backgroundColor: theme.colors.inputBg,
      color: theme.colors.text,
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 12,
      paddingHorizontal: 20,
      paddingVertical: 14,
      fontSize: 22,
      textAlign: 'center',
      width: '60%',
      marginBottom: 24,
      letterSpacing: 4,
    },
    btn: {
      backgroundColor: theme.colors.primary,
      borderRadius: 12,
      paddingVertical: 15,
      paddingHorizontal: 48,
      shadowColor: theme.colors.primary,
      shadowOpacity: 0.4,
      shadowRadius: 12,
      shadowOffset: { width: 0, height: 4 },
    },
    btnText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 16 },
  });
}
