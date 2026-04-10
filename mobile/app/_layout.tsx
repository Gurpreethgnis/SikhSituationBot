import { useEffect, useCallback, useState } from 'react';
import { LogBox, View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { Stack, useRouter, useSegments, Slot } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';
import { TranslationProvider } from '../contexts/TranslationContext';

LogBox.ignoreLogs([
  'Require cycle',
  'Non-serializable values were found in the navigation state',
  'expo-notifications',
  'Android Push notifications',
]);

SplashScreen.preventAutoHideAsync().catch(() => {});

// ---------------------------------------------------------------------------
// Auth gate — redirects based on auth state
// ---------------------------------------------------------------------------
function AuthGate() {
  const { token, user, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    const inAuthGroup = segments[0] === '(auth)';
    const inOnboarding = segments[0] === 'onboarding';

    if (!token) {
      if (!inAuthGroup) router.replace('/(auth)/login');
    } else if (user?.needs_birth_year && !inOnboarding) {
      router.replace('/onboarding');
    } else if (token && !user?.needs_birth_year && inAuthGroup) {
      router.replace('/(tabs)/chat');
    }
  }, [token, user, isLoading, segments]);

  return null;
}

// ---------------------------------------------------------------------------
// Inner layout (has access to theme context)
// ---------------------------------------------------------------------------
function InnerLayout() {
  const { theme } = useTheme();
  const { token } = useAuth();

  // Dynamically import notifications to avoid auto-registration errors in Expo Go
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
      <AuthGate />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding" options={{ presentation: 'modal', headerShown: false }} />
        <Stack.Screen name="shared/[shareId]" options={{ presentation: 'modal', headerShown: false }} />
      </Stack>
      <StatusBar style="auto" />
    </View>
  );
}

// ---------------------------------------------------------------------------
// Root layout — loads fonts and wraps providers
// ---------------------------------------------------------------------------
export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    'NotoSansGurmukhi': require('../assets/fonts/NotoSansGurmukhi-Regular.ttf'),
    'NotoSansGurmukhi-Bold': require('../assets/fonts/NotoSansGurmukhi-Bold.ttf'),
  });
  const [appIsReady, setAppIsReady] = useState(false);

  useEffect(() => {
    // Once fonts are loaded (or errored), mark app as ready
    if (fontsLoaded || fontError) {
      setAppIsReady(true);
    }
  }, [fontsLoaded, fontError]);

  // Fallback timeout in case fonts take too long
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!appIsReady) {
        console.warn('Font loading timeout, proceeding anyway');
        setAppIsReady(true);
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [appIsReady]);

  const onLayoutRootView = useCallback(async () => {
    if (appIsReady) {
      await SplashScreen.hideAsync();
    }
  }, [appIsReady]);

  // Show loading indicator while fonts are loading
  if (!appIsReady && !fontsLoaded) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingEmoji}>☬</Text>
        <ActivityIndicator size="large" color="#9b5de5" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }} onLayout={onLayoutRootView}>
      <AuthProvider>
        <ThemeProvider>
          <TranslationProvider>
            <InnerLayout />
          </TranslationProvider>
        </ThemeProvider>
      </AuthProvider>
    </View>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f0c1a',
  },
  loadingEmoji: {
    fontSize: 64,
    marginBottom: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#8a80a0',
  },
});
