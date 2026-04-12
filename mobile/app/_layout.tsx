import { useEffect } from 'react';
import { LogBox, View } from 'react-native';
import { Stack, useNavigationContainerRef, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';
import { TranslationProvider } from '../contexts/TranslationContext';

SplashScreen.preventAutoHideAsync().catch(() => {});

LogBox.ignoreLogs([
  'Require cycle',
  'Non-serializable values were found in the navigation state',
  'expo-notifications',
  'Android Push notifications',
]);

// ---------------------------------------------------------------------------
// Auth gate — redirects based on auth state
// ---------------------------------------------------------------------------
function AuthGate() {
  const { token, user, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const navRef = useNavigationContainerRef();

  useEffect(() => {
    if (isLoading) return;

    let cancelled = false;

    const applyRedirects = (): boolean => {
      if (!navRef.isReady()) return false;
      const inAuthGroup = segments[0] === '(auth)';
      const inOnboarding = segments[0] === 'onboarding';

      if (!token) {
        if (!inAuthGroup) router.replace('/(auth)/login');
      } else if (user?.needs_birth_year && !inOnboarding) {
        router.replace('/onboarding');
      } else if (token && !user?.needs_birth_year && inAuthGroup) {
        router.replace('/(tabs)/chat');
      }
      return true;
    };

    if (applyRedirects()) {
      return () => {
        cancelled = true;
      };
    }

    const id = setInterval(() => {
      if (cancelled) return;
      if (applyRedirects()) clearInterval(id);
    }, 32);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token, user, isLoading, segments, navRef, router]);

  return null;
}

// ---------------------------------------------------------------------------
// Shell: Stack first (navigator must mount before imperative redirects),
// then AuthGate (polls until NavigationContainer is ready).
// ---------------------------------------------------------------------------
function AppShell() {
  const { theme } = useTheme();
  const { token } = useAuth();

  useEffect(() => {
    import('../lib/notifications')
      .then(({ configureNotifications }) => configureNotifications())
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (token) {
      import('../lib/notifications')
        .then(({ registerForPushNotifications }) => registerForPushNotifications(token))
        .catch(() => {});
    }
  }, [token]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      {/*
        Stack must mount before any sibling calls router.replace, or Expo Router throws
        "Attempted to navigate before mounting the Root Layout component".
      */}
      <Stack screenOptions={{ headerShown: false, animation: 'default' }} />
      <AuthGate />
      <StatusBar style="auto" />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Root layout — fonts + splash
// ---------------------------------------------------------------------------
export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    'NotoSansGurmukhi': require('../assets/fonts/NotoSansGurmukhi-Regular.ttf'),
    'NotoSansGurmukhi-Bold': require('../assets/fonts/NotoSansGurmukhi-Bold.ttf'),
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded, fontError]);

  return (
    <View style={{ flex: 1, backgroundColor: '#0f0c1a' }}>
      <AuthProvider>
        <ThemeProvider>
          <TranslationProvider>
            <AppShell />
          </TranslationProvider>
        </ThemeProvider>
      </AuthProvider>
    </View>
  );
}

