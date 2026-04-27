import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Alert,
  SafeAreaView,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useTranslation } from '../contexts/TranslationContext';
import { useAuth } from '../contexts/AuthContext';

interface Chat {
  id: number;
  title: string;
  updated_at: string;
  created_at?: string;
}

interface Props {
  isOpen: boolean;
  chats: Chat[];
  activeChatId: number | null;
  onClose: () => void;
  onSelectChat: (chat: Chat) => void;
  onNewChat: () => void;
  onDeleteChat: (id: number) => void;
  user: any;
}

function groupByDate(chats: Chat[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
  const weekAgo = new Date(today); weekAgo.setDate(today.getDate() - 7);

  const groups: { label: string; data: Chat[] }[] = [];
  const todayChats = chats.filter(c => new Date(c.updated_at) >= today);
  const yestChats = chats.filter(c => { const d = new Date(c.updated_at); return d >= yesterday && d < today; });
  const weekChats = chats.filter(c => { const d = new Date(c.updated_at); return d >= weekAgo && d < yesterday; });
  const olderChats = chats.filter(c => new Date(c.updated_at) < weekAgo);

  if (todayChats.length) groups.push({ label: 'Today', data: todayChats });
  if (yestChats.length) groups.push({ label: 'Yesterday', data: yestChats });
  if (weekChats.length) groups.push({ label: 'Past 7 Days', data: weekChats });
  if (olderChats.length) groups.push({ label: 'Older', data: olderChats });
  return groups;
}

export default function Sidebar({
  isOpen, chats, activeChatId, onClose, onSelectChat, onNewChat, onDeleteChat, user,
}: Props) {
  const { theme } = useTheme();
  const { t } = useTranslation();
  const { signOut } = useAuth();
  const s = makeStyles(theme);

  const groups = groupByDate(chats);

  const confirmDelete = (chat: Chat) => {
    Alert.alert('Delete chat?', `"${chat.title}" will be removed.`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => onDeleteChat(chat.id) },
    ]);
  };

  const renderItem = ({ item }: { item: Chat }) => (
    <View style={s.chatRow}>
      <TouchableOpacity style={[s.chatBtn, item.id === activeChatId && s.chatBtnActive]} onPress={() => onSelectChat(item)}>
        <Text style={[s.chatTitle, item.id === activeChatId && s.chatTitleActive]} numberOfLines={1}>{item.title}</Text>
      </TouchableOpacity>
      <TouchableOpacity onPress={() => confirmDelete(item)} style={s.deleteBtn}>
        <Ionicons name="trash-outline" size={16} color={theme.colors.textMuted} />
      </TouchableOpacity>
    </View>
  );

  return (
    <Modal visible={isOpen} animationType="slide" transparent onRequestClose={onClose}>
      <View style={s.overlay}>
        <Pressable style={s.backdrop} onPress={onClose} />
        <SafeAreaView style={s.drawer}>
          {/* Header */}
          <View style={s.drawerHeader}>
            <Text style={s.drawerTitle}>☬ {t('appName')}</Text>
            <TouchableOpacity onPress={onClose} style={s.closeBtn}>
              <Ionicons name="close" size={22} color={theme.colors.text} />
            </TouchableOpacity>
          </View>

          {/* New chat */}
          <TouchableOpacity style={s.newChatBtn} onPress={onNewChat}>
            <Ionicons name="add" size={20} color={theme.colors.primary} />
            <Text style={s.newChatText}>{t('newChat')}</Text>
          </TouchableOpacity>

          {/* Chat groups */}
          <FlatList
            data={groups}
            keyExtractor={(item) => item.label}
            style={s.chatList}
            renderItem={({ item: group }) => (
              <View>
                <Text style={s.groupLabel}>{group.label}</Text>
                {group.data.map(chat => (
                  <View key={chat.id}>{renderItem({ item: chat })}</View>
                ))}
              </View>
            )}
            ListEmptyComponent={<Text style={s.emptyText}>No conversations yet</Text>}
          />

          {/* User info + sign out */}
          {user && (
            <View style={s.footer}>
              <Text style={s.userEmail} numberOfLines={1}>{user.email}</Text>
              <TouchableOpacity onPress={() => { onClose(); signOut(); }} style={s.signOutBtn}>
                <Ionicons name="log-out-outline" size={16} color={theme.colors.textMuted} />
                <Text style={s.signOutText}>{t('signOut')}</Text>
              </TouchableOpacity>
            </View>
          )}
        </SafeAreaView>
      </View>
    </Modal>
  );
}

function makeStyles(theme: ReturnType<typeof useTheme>['theme']) {
  return StyleSheet.create({
    overlay: { flex: 1, flexDirection: 'row' },
    backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)' },
    drawer: { width: 300, backgroundColor: theme.colors.background, borderRightWidth: 1, borderRightColor: theme.colors.border },
    drawerHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 20, borderBottomWidth: 1, borderBottomColor: theme.colors.border },
    drawerTitle: { fontSize: 18, fontWeight: '800', color: theme.colors.primary, letterSpacing: -0.5 },
    closeBtn: { padding: 4 },
    newChatBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, margin: 16, backgroundColor: theme.colors.surfaceAlt, borderRadius: 12, padding: 14, borderWidth: 1, borderColor: theme.colors.border },
    newChatText: { color: theme.colors.text, fontWeight: '700', fontSize: 15 },
    chatList: { flex: 1, paddingHorizontal: 10 },
    groupLabel: { fontSize: 11, fontWeight: '700', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.8, marginTop: 14, marginBottom: 6, paddingHorizontal: 8 },
    chatRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 2 },
    chatBtn: { flex: 1, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 10 },
    chatBtnActive: { backgroundColor: theme.colors.surfaceAlt },
    chatTitle: { fontSize: 14, color: theme.colors.text },
    chatTitleActive: { color: theme.colors.primary, fontWeight: '600' },
    deleteBtn: { padding: 8 },
    emptyText: { padding: 20, color: theme.colors.textMuted, fontSize: 14, textAlign: 'center' },
    footer: { borderTopWidth: 1, borderTopColor: theme.colors.border, padding: 14 },
    userEmail: { fontSize: 13, color: theme.colors.textMuted, marginBottom: 10 },
    signOutBtn: { flexDirection: 'row', alignItems: 'center', gap: 8 },
    signOutText: { fontSize: 14, color: theme.colors.textMuted },
  });
}
