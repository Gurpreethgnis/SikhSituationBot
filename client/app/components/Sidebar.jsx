'use client'

import React from 'react'
import Link from 'next/link'
import ThemeSwitcher from './ThemeSwitcher.jsx'
import './Sidebar.css'

function ChatGroup({ label, items, activeChatId, onSelectChat }) {
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
            <span className="history-text">{c.title || 'Chat'}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

function Sidebar({ chatGroups, onSelectChat, onNewChat, isOpen, session, activeChatId, onSignOut }) {
  const user = session?.user

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar__header">
        <button type="button" className="new-chat-btn" onClick={onNewChat}>
          <span className="plus-icon">+</span> New Chat
        </button>
      </div>

      <div className="sidebar__nav">
        <Link href="/parmaans" className="sidebar-link">
          Parmaans
        </Link>
        <Link href="/" className="sidebar-link">
          Home
        </Link>
        {user && (
          <Link href="/settings" className="sidebar-link">
            Settings
          </Link>
        )}
        {user?.isAdmin && (
          <Link href="/admin" className="sidebar-link">
            Admin
          </Link>
        )}
      </div>

      <div className="sidebar__history">
        <h3 className="history-label">Conversations</h3>
        {!session && <p className="no-history">Sign in to save chats by conversation.</p>}
        {session && (
          <>
            <ChatGroup
              label="Today"
              items={chatGroups?.today}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            <ChatGroup
              label="Yesterday"
              items={chatGroups?.yesterday}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            <ChatGroup
              label="Last 7 days"
              items={chatGroups?.week}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            <ChatGroup
              label="Older"
              items={chatGroups?.older}
              activeChatId={activeChatId}
              onSelectChat={onSelectChat}
            />
            {!chatGroups?.today?.length &&
              !chatGroups?.yesterday?.length &&
              !chatGroups?.week?.length &&
              !chatGroups?.older?.length && <p className="no-history">No saved chats yet.</p>}
          </>
        )}
      </div>

      <div className="sidebar__settings">
        <ThemeSwitcher compact />
      </div>

      <div className="sidebar__footer">
        {user ? (
          <div className="user-profile">
            <div className="user-avatar">{(user.name || user.email || '?').slice(0, 2).toUpperCase()}</div>
            <div className="user-meta">
              <span className="user-name">{user.name || user.email}</span>
              <button type="button" className="sign-out-btn" onClick={onSignOut}>
                Sign out
              </button>
            </div>
          </div>
        ) : (
          <div className="user-profile">
            <Link href="/login" className="sidebar-login-link">
              Sign in
            </Link>
          </div>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
