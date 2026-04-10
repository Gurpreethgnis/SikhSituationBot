import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ---------------------------------------------------------------------------
// Theme definitions — mirrors the 4 web themes
// ---------------------------------------------------------------------------
export interface Theme {
  id: string;
  label: string;
  colors: {
    background: string;
    surface: string;
    surfaceAlt: string;
    border: string;
    text: string;
    textMuted: string;
    primary: string;
    primaryText: string;
    userBubble: string;
    assistantBubble: string;
    inputBg: string;
    tabBar: string;
  };
}

export const THEMES: Theme[] = [
  {
    id: 'dark',
    label: 'Dark',
    colors: {
      background: '#0f0c1a',
      surface: '#1a1625',
      surfaceAlt: '#231d33',
      border: '#2e2845',
      text: '#e8e0f0',
      textMuted: '#8a80a0',
      primary: '#9b5de5',
      primaryText: '#ffffff',
      userBubble: '#2a1f4a',
      assistantBubble: '#1a1625',
      inputBg: '#231d33',
      tabBar: '#0f0c1a',
    },
  },
  {
    id: 'light',
    label: 'Light',
    colors: {
      background: '#f5f2ff',
      surface: '#ffffff',
      surfaceAlt: '#f0ecff',
      border: '#d4caee',
      text: '#1a1230',
      textMuted: '#6b5f8a',
      primary: '#7c3aed',
      primaryText: '#ffffff',
      userBubble: '#ede9ff',
      assistantBubble: '#ffffff',
      inputBg: '#f0ecff',
      tabBar: '#ffffff',
    },
  },
  {
    id: 'golden',
    label: 'Golden',
    colors: {
      background: '#1a1205',
      surface: '#221a08',
      surfaceAlt: '#2e2410',
      border: '#4a371a',
      text: '#f5e6c0',
      textMuted: '#a08040',
      primary: '#d4a017',
      primaryText: '#1a1205',
      userBubble: '#2e2010',
      assistantBubble: '#221a08',
      inputBg: '#2e2410',
      tabBar: '#1a1205',
    },
  },
  {
    id: 'forest',
    label: 'Forest',
    colors: {
      background: '#0a1a0f',
      surface: '#122018',
      surfaceAlt: '#1a2e20',
      border: '#2a4a35',
      text: '#d0ead8',
      textMuted: '#5a8a6a',
      primary: '#2d9e5f',
      primaryText: '#ffffff',
      userBubble: '#1a2e20',
      assistantBubble: '#122018',
      inputBg: '#1a2e20',
      tabBar: '#0a1a0f',
    },
  },
];

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
interface ThemeContextValue {
  theme: Theme;
  setThemeId: (id: string) => void;
  themes: Theme[];
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

const THEME_STORAGE_KEY = 'ssb_theme_id';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(THEMES[0]);

  useEffect(() => {
    AsyncStorage.getItem(THEME_STORAGE_KEY).then((id) => {
      if (id) {
        const found = THEMES.find((t) => t.id === id);
        if (found) setTheme(found);
      }
    });
  }, []);

  const setThemeId = (id: string) => {
    const found = THEMES.find((t) => t.id === id);
    if (found) {
      setTheme(found);
      AsyncStorage.setItem(THEME_STORAGE_KEY, id);
    }
  };

  return (
    <ThemeContext.Provider value={{ theme, setThemeId, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
}
