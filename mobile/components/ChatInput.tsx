import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  loading?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (v: string) => void;
  leftSlot?: React.ReactNode;
}

export default function ChatInput({
  onSend,
  disabled,
  loading,
  placeholder = 'Share your situation…',
  value,
  onChange,
  leftSlot,
}: ChatInputProps) {
  const { theme } = useTheme();
  const [internalText, setInternalText] = useState('');

  // Controlled/uncontrolled
  const controlled = value !== undefined && onChange !== undefined;
  const text = controlled ? value : internalText;
  const setText = controlled ? onChange! : setInternalText;

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    if (!controlled) setInternalText('');
  };

  const s = makeStyles(theme);

  return (
    <View style={s.row}>
      {leftSlot && <View style={s.leftSlot}>{leftSlot}</View>}
      <TextInput
        style={s.input}
        value={text}
        onChangeText={setText}
        placeholder={placeholder}
        placeholderTextColor={theme.colors.textMuted}
        multiline
        maxLength={2000}
        editable={!disabled}
        returnKeyType="send"
        blurOnSubmit={false}
        onSubmitEditing={handleSubmit}
      />
      <TouchableOpacity
        style={[s.sendBtn, (!text.trim() || disabled) && s.sendBtnDisabled]}
        onPress={handleSubmit}
        disabled={!text.trim() || disabled}
      >
        {loading ? (
          <ActivityIndicator size="small" color={theme.colors.primaryText} />
        ) : (
          <Ionicons name="send" size={18} color={theme.colors.primaryText} />
        )}
      </TouchableOpacity>
    </View>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    row: {
      flexDirection: 'row',
      alignItems: 'flex-end',
      backgroundColor: theme.colors.surfaceAlt,
      borderRadius: 26,
      borderWidth: 1,
      borderColor: theme.colors.border,
      paddingHorizontal: 12,
      paddingVertical: 6,
      gap: 8,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
      elevation: 5,
    },
    leftSlot: { justifyContent: 'flex-end', paddingBottom: 6 },
    input: {
      flex: 1,
      color: theme.colors.text,
      fontSize: 16,
      maxHeight: 120,
      paddingTop: 8,
      paddingBottom: 8,
      paddingHorizontal: 4,
    },
    sendBtn: {
      backgroundColor: theme.colors.primary,
      borderRadius: 18,
      width: 36,
      height: 36,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: 2,
    },
    sendBtnDisabled: {
      backgroundColor: theme.colors.border,
      opacity: 0.5,
    },
  });
}
