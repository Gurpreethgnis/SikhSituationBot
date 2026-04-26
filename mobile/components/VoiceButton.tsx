import React from 'react';
import { TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

interface VoiceButtonProps {
  onPress: () => void;
  active?: boolean;
  loading?: boolean;
  disabled?: boolean;
}

export default function VoiceButton({ onPress, active, loading, disabled }: VoiceButtonProps) {
  const { theme } = useTheme();

  return (
    <TouchableOpacity
      style={[
        styles.button,
        { backgroundColor: active ? '#2d1b4e' : theme.colors.inputBg, borderColor: active ? theme.colors.primary : theme.colors.border },
        disabled && styles.disabled
      ]}
      onPress={onPress}
      disabled={disabled || loading}
    >
      {loading ? (
        <ActivityIndicator size="small" color={theme.colors.primary} />
      ) : (
        <Ionicons
          name={active ? "mic" : "mic-outline"}
          size={22}
          color={active ? theme.colors.primary : theme.colors.textMuted}
        />
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 44,
    height: 44,
    borderRadius: 22,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabled: {
    opacity: 0.5,
  },
});
