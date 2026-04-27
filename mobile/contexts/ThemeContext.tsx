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
    id: 'basanti',
    label: 'Basanti (Orange)',
    colors: {
      background: '#1a1708',
      surface: '#2a2510',
      surfaceAlt: '#332d18',
      border: '#4a4220',
      text: '#fff8dc',
      textMuted: '#d4c896',
      primary: '#ffd700',
      primaryText: '#1a1708',
      userBubble: '#ffd700',
      assistantBubble: '#2a2510',
      inputBg: '#332d18',
      tabBar: '#1a1708',
    },
  },
  {
    id: 'neela',
    label: 'Neela (Blue)',
    colors: {
      background: '#0f172a',
      surface: '#1e293b',
      surfaceAlt: '#334155',
      border: '#334155',
      text: '#f8fafc',
      textMuted: '#94a3b8',
      primary: '#fbbf24',
      primaryText: '#0f172a',
      userBubble: '#fbbf24',
      assistantBubble: '#1e293b',
      inputBg: '#334155',
      tabBar: '#0f172a',
    },
  },
  {
    id: 'light',
    label: 'Light',
    colors: {
      background: '#f1f5f9',
      surface: '#ffffff',
      surfaceAlt: '#e2e8f0',
      border: '#cbd5e1',
      text: '#0f172a',
      textMuted: '#64748b',
      primary: '#d4af37',
      primaryText: '#f1f5f9',
      userBubble: '#d4af37',
      assistantBubble: '#ffffff',
      inputBg: '#e2e8f0',
      tabBar: '#f1f5f9',
    },
  },
  {
    id: 'khalsa-gold',
    label: 'Khalsa Gold',
    colors: {
      background: '#1c1410',
      surface: '#2d241e',
      surfaceAlt: '#3d322a',
      border: '#4d4038',
      text: '#fff8e7',
      textMuted: '#c9b896',
      primary: '#d4af37',
      primaryText: '#1c1410',
      userBubble: '#d4af37',
      assistantBubble: '#2d241e',
      inputBg: '#3d322a',
      tabBar: '#1c1410',
    },
  },
  {
    id: 'nihangs-navy',
    label: 'Nihangs Navy',
    colors: {
      background: '#0a0a1a',
      surface: '#141428',
      surfaceAlt: '#1e1e3c',
      border: '#2e2e5c',
      text: '#e0e0ff',
      textMuted: '#9090c0',
      primary: '#fde047',
      primaryText: '#0a0a1a',
      userBubble: '#fde047',
      assistantBubble: '#141428',
      inputBg: '#1e1e3c',
      tabBar: '#0a0a1a',
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
