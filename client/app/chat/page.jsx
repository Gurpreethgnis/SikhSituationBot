'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useSession, signOut } from 'next-auth/react'
import Link from 'next/link'
import ChatInput from '../components/ChatInput.jsx'
import Perspectives from '../components/Perspectives.jsx'
import GuidanceMenu from '../components/GuidanceMenu.jsx'
import Logo from '../components/Logo'
import Sidebar from '../components/Sidebar.jsx'
import MarkdownRenderer from '../components/MarkdownRenderer'
import { apiBase, authHeaders, LANGUAGE_OPTIONS } from '../../lib/api'
import { useTheme } from '../contexts/ThemeContext.jsx'
import { useTranslation, SUPPORTED_UI_LANGUAGES } from '../contexts/TranslationContext.jsx'
import '../App.css'

function groupChatsByDate(chats) {
  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startOfYesterday = new Date(startOfToday)
  startOfYesterday.setDate(startOfYesterday.getDate() - 1)
  const weekAgo = new Date(startOfToday)
  weekAgo.setDate(weekAgo.getDate() - 7)

  const groups = { today: [], yesterday: [], week: [], older: [] }
  for (const c of chats) {
    const d = new Date(c.updated_at || c.created_at)
    if (d >= startOfToday) groups.today.push(c)
    else if (d >= startOfYesterday) groups.yesterday.push(c)
    else if (d >= weekAgo) groups.week.push(c)
    else groups.older.push(c)
  }
  return groups
}

export default function ChatPage() {
  const { data: session } = useSession()
  const token = session?.accessToken
  const { setTheme, themes } = useTheme()
  const { t, uiLanguage, changeUiLanguage } = useTranslation()

  const [persona, setPersona] = useState('adult')
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [guidanceMode, setGuidanceMode] = useState('guidance')
  const [personaSource, setPersonaSource] = useState('default')
  const [shareStatus, setShareStatus] = useState('')

  const messagesEndRef = useRef(null)
  const baseUrl = apiBase()

  const handleShare = async () => {
    if (!activeChatId || !token) {
      setShareStatus('Please sign in to share')
      setTimeout(() => setShareStatus(''), 3000)
      return
    }
    try {
      setShareStatus('Creating share link...')
      const res = await fetch(`${baseUrl}/api/chats/${activeChatId}/share`, {
        method: 'POST',
        headers: authHeaders(token),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Failed to share')
      
      // Copy to clipboard
      await navigator.clipboard.writeText(data.url)
      setShareStatus('Link copied to clipboard!')
      setTimeout(() => setShareStatus(''), 3000)
    } catch (err) {
      console.error('Share error:', err)
      setShareStatus(err.message || 'Failed to share')
      setTimeout(() => setShareStatus(''), 3000)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const refreshChats = useCallback(async () => {
    if (!token) return
    try {
      const r = await fetch(`${baseUrl}/api/chats`, { headers: authHeaders(token) })
      if (!r.ok) return
      const d = await r.json()
      setChats(d.chats || [])
    } catch {
      /* ignore */
    }
  }, [baseUrl, token])

  useEffect(() => {
    if (token) refreshChats()
  }, [token, refreshChats])

  useEffect(() => {
    if (!token) return
    let cancelled = false
    ;(async () => {
      try {
        const r = await fetch(`${baseUrl}/api/auth/me`, { headers: authHeaders(token) })
        if (!r.ok || cancelled) return
        const d = await r.json()
        const u = d.user
        if (cancelled) return
        if (u?.preferred_language) setLanguage(u.preferred_language)
        if (u?.preferred_persona) setPersona(u.preferred_persona)
        if (u?.persona_source) setPersonaSource(u.persona_source)
        if (u?.preferred_theme && themes.some((t) => t.id === u.preferred_theme)) {
          setTheme(u.preferred_theme)
        }
      } catch {
        /* ignore */
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token, baseUrl, themes, setTheme])

  const handleNewChat = async () => {
    setMessages([])
    setSuggestions([])
    setError('')
    if (!token) {
      setActiveChatId(null)
      return
    }
    try {
      const r = await fetch(`${baseUrl}/api/chats`, {
        method: 'POST',
        headers: authHeaders(token),
        body: JSON.stringify({ title: 'New chat' }),
      })
      if (!r.ok) return
      const d = await r.json()
      setActiveChatId(d.chat.id)
      await refreshChats()
    } catch {
      /* ignore */
    }
  }

  const handleSelectChat = async (chat) => {
    if (!token) return
    setError('')
    setSuggestions([])
    try {
      const r = await fetch(`${baseUrl}/api/chats/${chat.id}`, { headers: authHeaders(token) })
      if (!r.ok) return
      const d = await r.json()
      const loaded = d.chat?.messages || []
      setActiveChatId(chat.id)
      setMessages(
        loaded.map((m) => ({
          role: m.role,
          content: m.content,
          shabad: m.shabad
            ? {
                text: m.shabad.gurmukhi,
                title: m.shabad.english_translation,
                transliteration: m.shabad.romanization,
                sttm_link: m.shabad.sttm_link,
              }
            : null,
          isQuestion: false,
        }))
      )
    } catch {
      /* ignore */
    }
    setSidebarOpen(false)
  }

  const handleShare = async () => {
    if (!token || !activeChatId) return
    try {
      const r = await fetch(`${baseUrl}/api/chats/${activeChatId}/share`, {
        method: 'POST',
        headers: authHeaders(token),
      })
      const d = await r.json()
      if (r.ok && d.url) {
        await navigator.clipboard.writeText(d.url)
        alert('Share link copied to clipboard.')
      }
    } catch {
      /* ignore */
    }
  }

  const handleSend = async (query) => {
    if (!token) {
      setError('Session expired. Please sign in again.')
      return
    }
    setError('')
    setLoading(true)

    const userMessage = { role: 'user', content: query }
    setMessages((prev) => [...prev, userMessage])

    const messageHistory = [...messages, userMessage].map((m) => ({
      role: m.role,
      content: m.content,
    }))

    try {
      let chatId = activeChatId
      if (token && !chatId) {
        const rc = await fetch(`${baseUrl}/api/chats`, {
          method: 'POST',
          headers: authHeaders(token),
          body: JSON.stringify({ title: 'New chat' }),
        })
        const dj = await rc.json().catch(() => ({}))
        if (rc.ok && dj.chat?.id) {
          chatId = dj.chat.id
          setActiveChatId(chatId)
          await refreshChats()
        }
      }

      const headers = { 'Content-Type': 'application/json' }
      if (token) headers.Authorization = `Bearer ${token}`

      const body = {
        query,
        persona,
        language,
        message_history: messageHistory.slice(-20),
        guidance_mode: guidanceMode,
      }
      if (chatId) body.chat_id = chatId

      const response = await fetch(`${baseUrl}/ask`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed: ${response.status}`)
      }

      const data = await response.json()

      if (data.error) {
        setError(data.error)
      } else {
        let content = data.response || ''
        let extractedSuggestions = []

        if (!content) {
          setError('No response received from the server. Please try again.')
          return
        }

        if (content.includes('[SUGGESTIONS]')) {
          const parts = content.split('[SUGGESTIONS]')
          content = parts[0].trim()
          const suggestionLines = parts[1].trim().split('\n')
          extractedSuggestions = suggestionLines
            .map((s) => s.replace(/^- /, '').trim())
            .filter((s) => s.length > 0)
        }

        const aiMessage = {
          role: 'assistant',
          content,
          shabad: data.shabad,
          persona: data.persona,
          isQuestion: data.is_clarification === true,
        }
        setMessages((prev) => [...prev, aiMessage])
        setSuggestions(extractedSuggestions)

        if (data.chat_title && token && chatId) {
          setChats((prev) => prev.map((c) => (c.id === chatId ? { ...c, title: data.chat_title } : c)))
          await refreshChats()
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion)
  }

  const chatGroups = groupChatsByDate(chats)

  return (
    <div className="app-container">
      <div className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} onClick={() => setSidebarOpen(false)} />
      <Sidebar
        chatGroups={chatGroups}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
        session={session}
        activeChatId={activeChatId}
        onSignOut={() => signOut({ callbackUrl: '/' })}
      />

      <main className="chat-main">
        <header className="chat-header desktop-only-header">
          <div className="chat-header-left">
            <Link href="/" className="chat-nav-link">
              Home
            </Link>
            <Link href="/parmaans" className="chat-nav-link">
              Parmaans
            </Link>
            {session?.user?.isAdmin && (
              <Link href="/admin" className="chat-nav-link">
                Admin
              </Link>
            )}
          </div>
          <div className="chat-header-right">
            <span className="active-mode-indicator" title={guidanceMode === 'guidance' ? t('guidanceModeHint') : t('parmaanModeHint')}>
              {guidanceMode === 'guidance' ? `📖 ${t('guidanceMode')}` : `🔍 ${t('parmaanMode')}`}
            </span>
            <select
              className="lang-select ui-lang-select"
              value={uiLanguage}
              onChange={(e) => {
                changeUiLanguage(e.target.value)
                setLanguage(e.target.value)
              }}
              aria-label="Interface language"
              title={t('language')}
            >
              {SUPPORTED_UI_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
            {token && activeChatId && (
              <button type="button" className="share-btn" onClick={handleShare}>
                {t('share')}
              </button>
            )}
            {session?.user && (
              <Link href="/settings" className="chat-nav-link settings-link" title={t('settings')}>
                ⚙️
              </Link>
            )}
          </div>
        </header>

        <header className="mobile-header">
          <button type="button" className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>
          <div className="mobile-header-logo">
            <Logo variant="compact" />
          </div>
        </header>

        <section className="chat-messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <Logo />
              <h1>{t('appName')}</h1>
              <p>{t('tagline')}</p>
              {personaSource === 'default' && (
                <Perspectives activePersona={persona} onPersonaChange={setPersona} />
              )}
              {personaSource === 'google' && (
                <p className="persona-from-profile-hint">
                  Response style (child / teen / adult) is set from your Google account birthday. You can change it in{' '}
                  <Link href="/settings">Settings</Link>.
                </p>
              )}
              {personaSource === 'manual' && (
                <p className="persona-from-profile-hint">
                  Response style is saved in <Link href="/settings">Settings</Link>. The bar above is hidden while you use
                  your saved choice.
                </p>
              )}
            </div>
          ) : (
            <div className="messages-thread">
              {messages.map((msg, index) => (
                <div key={index} className={`message message--${msg.role}`}>
                  <div className="message-label">{msg.role === 'user' ? t('you') : t('guru')}</div>
                  <div className="message-content">
                    <MarkdownRenderer content={msg.content} />
                    {msg.shabad?.sttm_link && (
                      <a
                        href={msg.shabad.sttm_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="sttm-link"
                      >
                        View on SikhiToTheMax ↗
                      </a>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message message--assistant loading">
                  <div className="message-label">{t('seekingWisdom')}</div>
                  <div className="message-content">
                    <div className="typing-dots">
                      <span />
                      <span />
                      <span />
                    </div>
                  </div>
                </div>
              )}
              {error && <div className="error-message">{error}</div>}
              
              {/* Share button - show after conversation */}
              {messages.length > 0 && !loading && (
                <div className="share-container">
                  <button 
                    type="button" 
                    className="share-btn"
                    onClick={handleShare}
                    disabled={!activeChatId}
                    title={activeChatId ? t('share') : 'Save chat first to share'}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                      <polyline points="16 6 12 2 8 6" />
                      <line x1="12" y1="2" x2="12" y2="15" />
                    </svg>
                    {t('share')}
                  </button>
                  {shareStatus && <span className="share-status">{shareStatus}</span>}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        <footer className="chat-footer">
          <div className="chat-input-wrapper">
            {suggestions.length > 0 && !loading && messages.length > 0 && (
              <div className="suggestions-bar">
                {suggestions.slice(0, 3).map((suggestion, i) => (
                  <button
                    key={i}
                    type="button"
                    className="suggestion-chip"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            <ChatInput
              onSend={handleSend}
              disabled={loading}
              loading={loading}
              startAdornment={
                <GuidanceMenu
                  mode={guidanceMode}
                  onModeChange={setGuidanceMode}
                  disabled={loading}
                  variant="embed"
                />
              }
            />
            <p className="footer-disclaimer" aria-live="polite">
              {t('disclaimer')}
            </p>
          </div>
        </footer>
      </main>
    </div>
  )
}
