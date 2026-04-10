import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { apiBase, authHeaders } from '../lib/api';
import { saveToken, getToken, deleteToken } from '../lib/secureStorage';

WebBrowser.maybeCompleteAuthSession();

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
// Provider
// ---------------------------------------------------------------------------
// Replace YOUR_EXPO_CLIENT_ID, YOUR_IOS_CLIENT_ID, YOUR_ANDROID_CLIENT_ID
// with real values from Google Cloud Console after creating OAuth 2.0 clients.
// See mobile/README.md for step-by-step setup instructions.
const GOOGLE_EXPO_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID || '';
const GOOGLE_IOS_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID || '';
const GOOGLE_ANDROID_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || '';
const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || '';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [googleRequest, googleResponse, promptGoogleAsync] = Google.useAuthRequest({
    clientId: GOOGLE_EXPO_CLIENT_ID,
    iosClientId: GOOGLE_IOS_CLIENT_ID,
    androidClientId: GOOGLE_ANDROID_CLIENT_ID,
    webClientId: GOOGLE_WEB_CLIENT_ID,
    scopes: ['profile', 'email'],
  });

  // Debug: log the redirect URI being used
  useEffect(() => {
    if (googleRequest) {
      console.log('=== Google OAuth Debug ===');
      console.log('Redirect URI:', googleRequest.redirectUri);
      console.log('Client ID:', googleRequest.clientId);
      console.log('Request URL:', googleRequest.url);
    }
  }, [googleRequest]);

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
    console.log('=== Google Auth Response ===');
    console.log('Response type:', googleResponse?.type);
    console.log('Full response:', JSON.stringify(googleResponse, null, 2));
    
    if (googleResponse?.type !== 'success') return;
    const { authentication } = googleResponse;
    if (!authentication?.accessToken) return;
    (async () => {
      try {
        // Fetch user info from Google
        const infoRes = await fetch('https://www.googleapis.com/userinfo/v2/me', {
          headers: { Authorization: `Bearer ${authentication.accessToken}` },
        });
        const googleUser = await infoRes.json();

        // Sync with Flask backend (upsert user, get JWT)
        const base = apiBase();
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
        const syncData = await syncRes.json();
        if (!syncRes.ok) throw new Error(syncData.error || 'OAuth sync failed');
        await _applyToken(syncData.token, syncData.user);
      } catch (err: any) {
        console.error('Google sign-in error:', err.message);
        throw err;
      }
    })();
  }, [googleResponse]);

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  const fetchMe = async (tok: string) => {
    const base = apiBase();
    const r = await fetch(`${base}/api/auth/me`, { headers: authHeaders(tok) });
    if (!r.ok) return;
    const d = await r.json();
    setUser(d.user);
  };

  const _applyToken = async (tok: string, profile?: UserProfile) => {
    await saveToken(tok);
    setToken(tok);
    if (profile) {
      setUser(profile);
    } else {
      await fetchMe(tok);
    }
  };

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------
  const signInEmail = useCallback(async (email: string, password: string) => {
    const base = apiBase();
    const r = await fetch(`${base}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Login failed');
    await _applyToken(d.token, d.user);
  }, []);

  const signInGoogle = useCallback(async () => {
    await promptGoogleAsync();
  }, [promptGoogleAsync]);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    const base = apiBase();
    const r = await fetch(`${base}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    });
    const d = await r.json();
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
