import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter, Link } from 'expo-router';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useTranslation } from '../../contexts/TranslationContext';

export default function RegisterScreen() {
  const { register } = useAuth();
  const { theme } = useTheme();
  const { t } = useTranslation();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const s = makeStyles(theme);

  const handleRegister = async () => {
    if (!email.trim() || !password || password.length < 8) {
      Alert.alert('Invalid input', 'Please enter a valid email and password (8+ characters).');
      return;
    }
    setLoading(true);
    try {
      await register(email.trim().toLowerCase(), password, name.trim() || undefined);
    } catch (err: any) {
      Alert.alert('Registration failed', err.message || 'Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={s.container}>
      <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
        <View style={s.header}>
          <Text style={s.khandaEmoji}>☬</Text>
          <Text style={s.title}>Create Account</Text>
          <Text style={s.subtitle}>Join {t('appName')}</Text>
        </View>

        <View style={s.field}>
          <Text style={s.label}>{t('name')}</Text>
          <TextInput
            style={s.input}
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
            placeholder="Your name"
            placeholderTextColor={theme.colors.textMuted}
          />
        </View>

        <View style={s.field}>
          <Text style={s.label}>{t('email')}</Text>
          <TextInput
            style={s.input}
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="you@example.com"
            placeholderTextColor={theme.colors.textMuted}
          />
        </View>

        <View style={s.field}>
          <Text style={s.label}>{t('password')}</Text>
          <TextInput
            style={s.input}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholder="8+ characters"
            placeholderTextColor={theme.colors.textMuted}
          />
        </View>

        <TouchableOpacity style={s.primaryBtn} onPress={handleRegister} disabled={loading}>
          {loading ? <ActivityIndicator color={theme.colors.primaryText} /> : <Text style={s.primaryBtnText}>{t('register')}</Text>}
        </TouchableOpacity>

        <View style={s.footer}>
          <Text style={s.footerText}>{t('haveAccount')} </Text>
          <Link href="/(auth)/login" asChild>
            <TouchableOpacity>
              <Text style={s.footerLink}>{t('signIn')}</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    scroll: { flexGrow: 1, padding: 28, justifyContent: 'center' },
    header: { alignItems: 'center', marginBottom: 36 },
    khandaEmoji: { fontSize: 48, marginBottom: 12 },
    title: { fontSize: 26, fontWeight: '700', color: theme.colors.text },
    subtitle: { fontSize: 14, color: theme.colors.textMuted, marginTop: 6 },
    field: { marginBottom: 16 },
    label: { fontSize: 13, color: theme.colors.textMuted, marginBottom: 6, fontWeight: '600' },
    input: {
      backgroundColor: theme.colors.inputBg,
      color: theme.colors.text,
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 10,
      paddingHorizontal: 14,
      paddingVertical: 12,
      fontSize: 15,
    },
    primaryBtn: {
      backgroundColor: theme.colors.primary,
      borderRadius: 12,
      paddingVertical: 15,
      alignItems: 'center',
      marginTop: 8,
      shadowColor: theme.colors.primary,
      shadowOpacity: 0.4,
      shadowRadius: 12,
      shadowOffset: { width: 0, height: 4 },
    },
    primaryBtnText: { color: theme.colors.primaryText, fontWeight: '700', fontSize: 16 },
    footer: { flexDirection: 'row', justifyContent: 'center', marginTop: 28 },
    footerText: { color: theme.colors.textMuted, fontSize: 14 },
    footerLink: { color: theme.colors.primary, fontWeight: '600', fontSize: 14 },
  });
}
