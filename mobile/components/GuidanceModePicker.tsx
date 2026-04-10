import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useTranslation } from '../contexts/TranslationContext';
import type { GuidanceMode } from '../lib/api';

interface Props {
  mode: GuidanceMode;
  onModeChange: (mode: GuidanceMode) => void;
  disabled?: boolean;
}

export default function GuidanceModePicker({ mode, onModeChange, disabled }: Props) {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const s = makeStyles(theme);

  return (
    <View style={s.container}>
      <TouchableOpacity
        style={[s.btn, mode === 'guidance' && s.btnActive]}
        onPress={() => onModeChange('guidance')}
        disabled={disabled}
      >
        <Text style={[s.btnText, mode === 'guidance' && s.btnTextActive]}>📖</Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[s.btn, mode === 'parmaan' && s.btnActive]}
        onPress={() => onModeChange('parmaan')}
        disabled={disabled}
      >
        <Text style={[s.btnText, mode === 'parmaan' && s.btnTextActive]}>🔍</Text>
      </TouchableOpacity>
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    container: { flexDirection: 'column', gap: 4, paddingBottom: 2 },
    btn: {
      width: 30,
      height: 30,
      borderRadius: 8,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.colors.surfaceAlt,
      borderWidth: 1,
      borderColor: theme.colors.border,
    },
    btnActive: {
      backgroundColor: theme.colors.primary,
      borderColor: theme.colors.primary,
    },
    btnText: { fontSize: 14 },
    btnTextActive: {},
  });
}
