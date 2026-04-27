import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { Platform } from 'react-native';
import Constants, { ExecutionEnvironment } from 'expo-constants';
import type { AuthSessionResult } from 'expo-auth-session';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { requireApiBase, authHeaders, parseJsonResponse } from '../lib/api';
import { saveToken, getToken, deleteToken } from '../lib/secureStorage';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface UserProfile {
  id: number;
  email: string;
  name?: string;
  avatar_url?: string;
  is_admin: boolean;
  birth_year?: number;
  preferred_language: string;
  preferred_theme?: string;
  memory_enabled: boolean;
  memory_retention_days: number;
  needs_birth_year?: boolean;
}

interface AuthContextValue {
  token: string | null;
  user: UserProfile | null;
  isLoading: boolean;
  signInEmail: (email: string, password: string) => Promise<void>;
  signInGoogle: () => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

// ---------------------------------------------------------------------------
// Google OAuth env — expo-auth-session throws if the active platform client id is undefined.
// ---------------------------------------------------------------------------
const GOOGLE_EXPO_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID || '';
const GOOGLE_IOS_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || '';
const GOOGLE_ANDROID_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || '';
const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || '';

/** True if any Google OAuth client id is set (aligned with web: one `GOOGLE_CLIENT_ID` is enough). */
function hasGoogleClientConfigured(): boolean {
  return Boolean(
    GOOGLE_EXPO_CLIENT_ID ||
      GOOGLE_WEB_CLIENT_ID ||
      GOOGLE_IOS_CLIENT_ID ||
      GOOGLE_ANDROID_CLIENT_ID
  );
}

/**
 * expo-auth-session uses a browser-based OAuth flow. On Android, Google's **Android**
 * OAuth client type does NOT support custom URI schemes ("Custom URI scheme is not
 * enabled for your Android client"). Instead, use the **Web** client ID with Expo's
 * auth proxy (`https://auth.expo.io/@owner/slug`).
 *
 * iOS native builds can use an **iOS** OAuth client (bundle ID redirect works).
 * Android must use Web client + Expo proxy, OR switch to @react-native-google-signin.
 *
 * @see https://docs.expo.dev/guides/authentication/#google
 */
function buildGoogleRedirectUriOptions(): Record<string, string> {
  if (Platform.OS === 'web') return {};

  const owner = Constants.expoConfig?.owner;
  const slug = Constants.expoConfig?.slug;

  // iOS with native client: let expo-auth-session use bundle ID redirect
  if (Platform.OS === 'ios' && GOOGLE_IOS_CLIENT_ID) {
    return {};
  }

  // Android: Must use Expo's HTTPS proxy with Web client ID because Android OAuth
  // clients don't support custom URI schemes in browser-based flows.
  // This works in both Expo Go and dev client builds.
  if (Platform.OS === 'android' && owner && slug) {
    return { native: `https://auth.expo.io/@${owner}/${slug}` };
  }

  // Expo Go fallback for iOS without native client
  const isExpoGo = Constants.executionEnvironment === ExecutionEnvironment.StoreClient;
  if (isExpoGo && owner && slug) {
    return { native: `https://auth.expo.io/@${owner}/${slug}` };
  }

  return {};
}

// ---------------------------------------------------------------------------
// Provider — split so `Google.useAuthRequest` is only called when config exists.
// ---------------------------------------------------------------------------
export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Defer past cold start: calling at module scope has caused EXC_BAD_ACCESS on
  // NSURLSession-delegate (expo-web-browser / ASWebAuthenticationSession teardown).
  useEffect(() => {
    WebBrowser.maybeCompleteAuthSession();
  }, []);

  if (hasGoogleClientConfigured()) {
    return <AuthProviderWithGoogle>{children}</AuthProviderWithGoogle>;
  }
  return <AuthProviderWithoutGoogle>{children}</AuthProviderWithoutGoogle>;
}

function AuthProviderWithoutGoogle({ children }: { children: React.ReactNode }) {
  const promptGoogleAsync = useCallback(async () => {
    throw new Error(
      'Google Sign-In is not configured. Set GOOGLE_CLIENT_ID in the repo root .env (same as the web app), run `cd mobile && npm run sync-env`, then restart Expo with `npx expo start --clear`. Optional: add native iOS/Android OAuth client IDs in Google Cloud for production builds.'
    );
  }, []);

  return (
    <AuthProviderImpl googleResponse={null} promptGoogleAsync={promptGoogleAsync}>
      {children}
    </AuthProviderImpl>
  );
}

function AuthProviderWithGoogle({ children }: { children: React.ReactNode }) {
  // expo-auth-session on Android requires the Web client ID (Android OAuth clients don't
  // support custom URI schemes in browser-based flows). iOS can use native iOS client.
  // The Web client ID is used with Expo's auth proxy: https://auth.expo.io/@owner/slug
  const sharedClientId = GOOGLE_EXPO_CLIENT_ID || GOOGLE_WEB_CLIENT_ID || undefined;
  const redirectUriOptions = useMemo(() => buildGoogleRedirectUriOptions(), []);

  // For Android, force Web client ID since Android OAuth clients reject custom schemes
  const androidClientId = Platform.OS === 'android' ? (GOOGLE_WEB_CLIENT_ID || undefined) : (GOOGLE_ANDROID_CLIENT_ID || undefined);

  const [googleRequest, googleResponse, promptGoogleAsync] = Google.useAuthRequest(
    {
      clientId: sharedClientId,
      iosClientId: GOOGLE_IOS_CLIENT_ID || undefined,
      androidClientId,
      webClientId: GOOGLE_WEB_CLIENT_ID || undefined,
      scopes: ['profile', 'email'],
    },
    redirectUriOptions
  );

  useEffect(() => {
    if (__DEV__ && googleRequest) {
      console.log('[Google OAuth] Full config:');
      console.log('  redirectUri:', googleRequest.redirectUri);
      console.log('  clientId:', googleRequest.clientId);
      console.log('  url:', googleRequest.url);
    }
  }, [googleRequest]);

  useEffect(() => {
    if (Constants.executionEnvironment === ExecutionEnvironment.StoreClient) return;
    if (!GOOGLE_WEB_CLIENT_ID) return;
    if (Platform.OS === 'ios' && !GOOGLE_IOS_CLIENT_ID) {
      console.warn(
        '[Google Sign-In] Native iOS: set EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID (OAuth client type iOS, bundle com.gianiji.app). See mobile/docs/GOOGLE_OAUTH_PRODUCTION.md'
      );
    }
  }, []);

  return (
    <AuthProviderImpl googleResponse={googleResponse} promptGoogleAsync={promptGoogleAsync}>
      {children}
    </AuthProviderImpl>
  );
}

function AuthProviderImpl({
  children,
  googleResponse,
  promptGoogleAsync,
}: {
  children: React.ReactNode;
  googleResponse: AuthSessionResult | null;
  promptGoogleAsync: () => Promise<AuthSessionResult>;
}) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // ------------------------------------------------------------------
  // Bootstrap: load stored token on app start
  // ------------------------------------------------------------------
  useEffect(() => {
    (async () => {
      try {
        const stored = await getToken();
        if (stored) {
          setToken(stored);
          await fetchMe(stored);
        }
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // ------------------------------------------------------------------
  // Handle Google auth response
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!googleResponse) return;
    console.log('=== Google Auth Response ===');
    console.log('Response type:', googleResponse?.type);
    console.log('Full response:', JSON.stringify(googleResponse, null, 2));

    if (googleResponse?.type !== 'success') return;
    const { authentication } = googleResponse;
    if (!authentication?.accessToken) return;
    (async () => {
      try {
        const infoRes = await fetch('https://www.googleapis.com/userinfo/v2/me', {
          headers: { Authorization: `Bearer ${authentication.accessToken}` },
        });
        const googleUser = await infoRes.json();

        const base = requireApiBase();
        const syncRes = await fetch(`${base}/api/auth/oauth-sync`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Internal-Key': process.env.EXPO_PUBLIC_FLASK_INTERNAL_KEY || '',
          },
          body: JSON.stringify({
            email: googleUser.email,
            name: googleUser.name,
            avatar_url: googleUser.picture,
          }),
        });
        const syncData = (await parseJsonResponse(syncRes)) as { error?: string; token?: string; user?: UserProfile };
        if (!syncRes.ok) throw new Error(syncData.error || 'OAuth sync failed');
        await _applyToken(syncData.token, syncData.user);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        console.error('Google sign-in error:', message);
      }
    })();
  }, [googleResponse]);

  const fetchMe = async (tok: string) => {
    const base = requireApiBase();
    const r = await fetch(`${base}/api/auth/me`, { headers: authHeaders(tok) });
    if (!r.ok) return;
    const d = (await parseJsonResponse(r)) as { user: UserProfile };
    setUser(d.user);
  };

  const _applyToken = async (tok: string | undefined, profile?: UserProfile) => {
    if (!tok) return;
    await saveToken(tok);
    setToken(tok);
    if (profile) {
      setUser(profile);
    } else {
      await fetchMe(tok);
    }
  };

  const signInEmail = useCallback(async (email: string, password: string) => {
    const base = requireApiBase();
    const r = await fetch(`${base}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const d = (await parseJsonResponse(r)) as { error?: string; token: string; user: UserProfile };
    if (!r.ok) throw new Error(d.error || 'Login failed');
    await _applyToken(d.token, d.user);
  }, []);

  const signInGoogle = useCallback(async () => {
    await promptGoogleAsync();
  }, [promptGoogleAsync]);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    const base = requireApiBase();
    const r = await fetch(`${base}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    });
    const d = (await parseJsonResponse(r)) as { error?: string; token: string; user: UserProfile };
    if (!r.ok) throw new Error(d.error || 'Registration failed');
    await _applyToken(d.token, d.user);
  }, []);

  const signOut = useCallback(async () => {
    await deleteToken();
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (token) await fetchMe(token);
  }, [token]);

  return (
    <AuthContext.Provider value={{ token, user, isLoading, signInEmail, signInGoogle, register, signOut, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}
