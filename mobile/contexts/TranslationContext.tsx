import React, { createContext, useContext, useState, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ---------------------------------------------------------------------------
// Supported UI languages — mirrors web TranslationContext
// ---------------------------------------------------------------------------
export const SUPPORTED_UI_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'zh', label: '中文' },
  { code: 'ar', label: 'العربية' },
];

// ---------------------------------------------------------------------------
// Translation strings — English base + overrides per language
// ---------------------------------------------------------------------------
type TranslationKey = keyof typeof EN_STRINGS;

const EN_STRINGS = {
  appName: 'Giani Ji',
  tagline: 'Receive guidance from Gurbani for your life situation',
  you: 'You',
  guru: 'Giani Ji',
  signIn: 'Sign In',
  signUp: 'Sign Up',
  signOut: 'Sign Out',
  email: 'Email',
  password: 'Password',
  name: 'Name (optional)',
  login: 'Log In',
  register: 'Register',
  orContinueWith: 'or continue with',
  continueWithGoogle: 'Continue with Google',
  noAccount: "Don't have an account?",
  haveAccount: 'Already have an account?',
  typeYourMessage: 'Share your situation…',
  sendMessage: 'Send',
  search: 'Search',
  settings: 'Settings',
  language: 'Language',
  theme: 'Theme',
  birthYear: 'Year of birth',
  savePreferences: 'Save preferences',
  saving: 'Saving…',
  saved: 'Saved.',
  guidanceMode: 'Guidance',
  parmaanMode: 'Parmaan',
  guidanceModeHint: 'Receive spiritual guidance grounded in Gurbani',
  parmaanModeHint: 'Explore and search Gurbani verses directly',
  parmaanLibraryLink: 'Gurbani Library',
  knowledgeShabadCount: '{count} shabads in knowledge base',
  knowledgeShabadCountTitle: 'Number of Gurbani verses indexed',
  seekingWisdom: 'Seeking wisdom…',
  copyMessage: 'Copy',
  copyMessageDone: 'Copied!',
  share: 'Share',
  feedbackButton: 'Feedback',
  signInToSave: 'Sign in to save conversations.',
  newChat: 'New Chat',
  chatHistory: 'Chat History',
  today: 'Today',
  yesterday: 'Yesterday',
  pastWeek: 'Past 7 Days',
  older: 'Older',
  deleteChat: 'Delete',
  parmaanLinePlaceholder: 'Enter a line of Gurbani to find…',
  parmaanThemePlaceholder: 'Enter a theme or concept…',
  parmaanMessagePlaceholder: 'Ask about a Gurbani verse…',
  parmaanDiscoverySimilar: 'Similar',
  parmaanDiscoveryTopic: 'By Topic',
  parmaanDiscoveryContrasts: 'Contrasts',
  parmaanResultsHint: 'Select a verse below to explore it further',
  parmaanDisambiguationContextNote: 'Finding {discovery} verses ({count} results)',
  viewOnSikhiToTheMax: 'View on SikhiToTheMax ↗',
  memoryEnabled: 'Remember context across conversations',
  memoryRetentionDays: 'Keep memories for (days)',
  viewMemories: 'View saved memories',
  hideMemories: 'Hide saved memories',
  clearAllMemories: 'Clear all memories',
  noMemoriesYet: 'No saved memories yet.',
  removeMemory: 'Remove',
  onboardingTitle: 'One quick step',
  onboardingSubtitle: 'What year were you born? This helps us tailor responses for your age group.',
  onboardingContinue: 'Continue',
  adminPanel: 'Admin',
  sharedChat: 'Shared Conversation',
  loadingSharedChat: 'Loading conversation…',
  sharedChatNotFound: 'Conversation not found or no longer shared.',
  errorGeneric: 'Something went wrong. Please try again.',
  connecting: 'Connecting...',
  listening: "I'm listening...",
  thinking: 'Thinking...',
  speaking: 'Speaking...',
};

const PA_STRINGS: Partial<typeof EN_STRINGS> = {
  appName: 'ਗਿਆਨੀ ਜੀ',
  tagline: 'ਆਪਣੀ ਜੀਵਨ-ਸਥਿਤੀ ਲਈ ਗੁਰਬਾਣੀ ਤੋਂ ਮਾਰਗਦਰਸ਼ਨ ਪ੍ਰਾਪਤ ਕਰੋ',
  you: 'ਤੁਸੀਂ',
  guru: 'ਗਿਆਨੀ ਜੀ',
  guidanceMode: 'ਮਾਰਗਦਰਸ਼ਨ',
  parmaanMode: 'ਪ੍ਰਮਾਣ',
  seekingWisdom: 'ਗਿਆਨ ਦੀ ਭਾਲ…',
};

const HI_STRINGS: Partial<typeof EN_STRINGS> = {
  appName: 'ज्ञानी जी',
  tagline: 'अपनी जीवन स्थिति के लिए गुरबाणी से मार्गदर्शन प्राप्त करें',
  you: 'आप',
  guru: 'गिआनी जी',
  guidanceMode: 'मार्गदर्शन',
  parmaanMode: 'प्रमाण',
  seekingWisdom: 'ज्ञान की खोज…',
};

const TRANSLATIONS: Record<string, Partial<typeof EN_STRINGS>> = {
  en: EN_STRINGS,
  pa: PA_STRINGS,
  hi: HI_STRINGS,
};

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
interface TranslationContextValue {
  t: (key: TranslationKey) => string;
  uiLanguage: string;
  changeUiLanguage: (code: string) => void;
}

const TranslationContext = createContext<TranslationContextValue | null>(null);

export function useTranslation(): TranslationContextValue {
  const ctx = useContext(TranslationContext);
  if (!ctx) throw new Error('useTranslation must be used within TranslationProvider');
  return ctx;
}

const LANG_STORAGE_KEY = 'ssb_ui_language';

export function TranslationProvider({ children }: { children: React.ReactNode }) {
  const [uiLanguage, setUiLanguage] = useState('en');

  React.useEffect(() => {
    AsyncStorage.getItem(LANG_STORAGE_KEY).then((lang) => {
      if (lang && SUPPORTED_UI_LANGUAGES.some((l) => l.code === lang)) {
        setUiLanguage(lang);
      }
    });
  }, []);

  const t = useCallback(
    (key: TranslationKey): string => {
      const langStrings = TRANSLATIONS[uiLanguage] || {};
      return (langStrings[key] as string) || EN_STRINGS[key] || key;
    },
    [uiLanguage]
  );

  const changeUiLanguage = useCallback((code: string) => {
    setUiLanguage(code);
    AsyncStorage.setItem(LANG_STORAGE_KEY, code);
  }, []);

  return (
    <TranslationContext.Provider value={{ t, uiLanguage, changeUiLanguage }}>
      {children}
    </TranslationContext.Provider>
  );
}
