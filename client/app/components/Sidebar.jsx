'use client'

import React from 'react'
import Link from 'next/link'
import ThemeSwitcher from './ThemeSwitcher.jsx'
import { useTranslation } from '../contexts/TranslationContext.jsx'
import './Sidebar.css'

function ChatGroup({ label, items, activeChatId, onSelectChat }) {
  const { t } = useTranslation()
  if (!items?.length) return null
  return (
    <div className="sidebar__group">
      <h4 className="sidebar__group-label">{label}</h4>
      <div className="history-list">
        {items.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`history-item ${activeChatId === c.id ? 'active' : ''}`}
            onClick={() => onSelectChat(c)}
          >
            <span className="chat-icon">💬</span>
            <span className="history-text">{c.title || t('chat')}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function Sidebar({ chatGroups, onSelectChat, onNewChat, isOpen, session, activeChatId, onSignOut }) {
  const user = session?.user
  const { t } = useTranslation()

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar__header">
        <button type="button" className="new-chat-btn" onClick={onNewChat}>
          <span className="plus-icon">+</span> {t('newChat')}
        </button>
      </div>

      <div className="sidebar__nav">
        {user?.isAdmin && (
          <Link href="/admin" className="sidebar-link">
            {t('admin')}
          </Link>
        )}
      </div>

      <div className="sidebar__history">
        <h3 className="history-label">{t('conversations')}</h3>
        {!session && <p className="no-history">{t('signInToSave')}</p>}
        {session && (
          <>
            <ChatGroup
              label={t('today')}
              items={chatGroups?.today}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            <ChatGroup
              label={t('yesterday')}
              items={chatGroups?.yesterday}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            <ChatGroup
              label={t('last7Days')}
              items={chatGroups?.week}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            <ChatGroup
              label={t('older')}
              items={chatGroups?.older}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            {!chatGroups?.today?.length &&
              !chatGroups?.yesterday?.length &&
              !chatGroups?.week?.length &&
              !chatGroups?.older?.length && <p className="no-history">{t('noSavedChats')}</p>}
          </>
        )}
      </div>

      <div className="sidebar__settings">
        <div className="sidebar__settings-row">
          <span className="sidebar__settings-label">{t('theme')}</span>
          <ThemeSwitcher compact />
        </div>
      </div>

      <div className="sidebar__footer">
        {user ? (
          <div className="user-profile">
            <div className="user-avatar">{(user.name || user.email || '?').slice(0, 2).toUpperCase()}</div>
            <div className="user-meta">
              <span className="user-name">{user.name || user.email}</span>
              <button type="button" className="sign-out-btn" onClick={onSignOut}>
                {t('signOut')}
              </button>
            </div>
          </div>
        ) : (
          <div className="user-profile">
            <Link href="/login" className="sidebar-login-link">
              {t('signIn')}
            </Link>
          </div>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
