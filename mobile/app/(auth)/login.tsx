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
import { Ionicons } from '@expo/vector-icons';

export default function LoginScreen() {
  const { signInEmail, signInGoogle } = useAuth();
  const { theme } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const s = makeStyles(theme);

  const handleEmailLogin = async () => {
    if (!email.trim() || !password) {
      Alert.alert('Missing fields', 'Please enter your email and password.');
      return;
    }
    setLoading(true);
    try {
      await signInEmail(email.trim().toLowerCase(), password);
    } catch (err: any) {
      Alert.alert('Sign in failed', err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      await signInGoogle();
    } catch (err: any) {
      Alert.alert('Google sign-in failed', err.message || 'Please try again');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={s.container}>
      <ScrollView contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
        {/* Logo / Title */}
        <View style={s.header}>
          <Text style={s.khandaEmoji}>☬</Text>
          <Text style={s.title}>{t('appName')}</Text>
          <Text style={s.subtitle}>{t('tagline')}</Text>
        </View>

        {/* Email */}
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

        {/* Password */}
        <View style={s.field}>
          <Text style={s.label}>{t('password')}</Text>
          <View style={s.passwordRow}>
            <TextInput
              style={[s.input, { flex: 1 }]}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              placeholder="••••••••"
              placeholderTextColor={theme.colors.textMuted}
            />
            <TouchableOpacity onPress={() => setShowPassword((v) => !v)} style={s.eyeBtn}>
              <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color={theme.colors.textMuted} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Login button */}
        <TouchableOpacity style={s.primaryBtn} onPress={handleEmailLogin} disabled={loading}>
          {loading ? <ActivityIndicator color={theme.colors.primaryText} /> : <Text style={s.primaryBtnText}>{t('login')}</Text>}
        </TouchableOpacity>

        {/* Divider */}
        <View style={s.divider}>
          <View style={s.dividerLine} />
          <Text style={s.dividerText}>{t('orContinueWith')}</Text>
          <View style={s.dividerLine} />
        </View>

        {/* Google button */}
        <TouchableOpacity style={s.googleBtn} onPress={handleGoogleLogin} disabled={googleLoading}>
          {googleLoading ? (
            <ActivityIndicator color={theme.colors.text} />
          ) : (
            <>
              <Text style={s.googleIcon}>G</Text>
              <Text style={s.googleBtnText}>{t('continueWithGoogle')}</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Register link */}
        <View style={s.footer}>
          <Text style={s.footerText}>{t('noAccount')} </Text>
          <Link href="/(auth)/register" asChild>
            <TouchableOpacity>
              <Text style={s.footerLink}>{t('signUp')}</Text>
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
    header: { alignItems: 'center', marginBottom: 40 },
    khandaEmoji: { fontSize: 56, marginBottom: 12 },
    title: { fontSize: 26, fontWeight: '700', color: theme.colors.text, textAlign: 'center' },
    subtitle: { fontSize: 14, color: theme.colors.textMuted, textAlign: 'center', marginTop: 8, lineHeight: 20 },
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
    passwordRow: { flexDirection: 'row', alignItems: 'center' },
    eyeBtn: { position: 'absolute', right: 12 },
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
    divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 22 },
    dividerLine: { flex: 1, height: 1, backgroundColor: theme.colors.border },
    dividerText: { color: theme.colors.textMuted, marginHorizontal: 12, fontSize: 13 },
    googleBtn: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'center',
      borderWidth: 1,
      borderColor: theme.colors.border,
      borderRadius: 12,
      paddingVertical: 14,
      backgroundColor: theme.colors.surface,
      gap: 10,
    },
    googleIcon: { fontWeight: '900', fontSize: 18, color: '#4285F4' },
    googleBtnText: { color: theme.colors.text, fontWeight: '600', fontSize: 15 },
    footer: { flexDirection: 'row', justifyContent: 'center', marginTop: 28 },
    footerText: { color: theme.colors.textMuted, fontSize: 14 },
    footerLink: { color: theme.colors.primary, fontWeight: '600', fontSize: 14 },
  });
}
