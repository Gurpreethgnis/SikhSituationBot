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
      backgroundColor: theme.colors.inputBg,
      borderRadius: 16,
      borderWidth: 1,
      borderColor: theme.colors.border,
      paddingHorizontal: 8,
      paddingVertical: 6,
      gap: 6,
    },
    leftSlot: { justifyContent: 'flex-end', paddingBottom: 2 },
    input: {
      flex: 1,
      color: theme.colors.text,
      fontSize: 15,
      maxHeight: 120,
      paddingTop: 6,
      paddingBottom: 6,
      paddingHorizontal: 4,
    },
    sendBtn: {
      backgroundColor: theme.colors.primary,
      borderRadius: 10,
      width: 36,
      height: 36,
      alignItems: 'center',
      justifyContent: 'center',
    },
    sendBtnDisabled: { opacity: 0.4 },
  });
}
