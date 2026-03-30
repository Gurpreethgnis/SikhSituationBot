'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useSession, signOut } from 'next-auth/react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import ChatInput from '../components/ChatInput.jsx'
import GuidanceMenu from '../components/GuidanceMenu.jsx'
import ParmaanDiscoveryBar from '../components/ParmaanDiscoveryBar.jsx'
import Logo from '../components/Logo'
import Sidebar from '../components/Sidebar.jsx'
import MarkdownRenderer from '../components/MarkdownRenderer'
import FeedbackButton from '../components/FeedbackButton.jsx'
import FeedbackModal from '../components/FeedbackModal.jsx'
import { apiBase, authHeaders } from '../../lib/api'
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

const ASK_TIMEOUT_MS = 120_000

/** Parmaan responses embed per-shabad STTM links in markdown; skip redundant footer link. */
function contentHasParmaanVerbatimBlocks(content) {
  return typeof content === 'string' && content.includes('## Retrieved Gurbani')
}

function truncateText(s, n) {
  if (!s || s.length <= n) return s || ''
  return `${s.slice(0, n).trim()}…`
}

export default function ChatPage() {
  const { data: session, status: sessionStatus } = useSession()
  const token = session?.accessToken
  const router = useRouter()
  const { setTheme, themes } = useTheme()
  const { t, uiLanguage, changeUiLanguage } = useTranslation()

  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [chats, setChats] = useState([])
  const [activeChatId, setActiveChatId] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [guidanceMode, setGuidanceMode] = useState('guidance')
  const [parmaanDiscoveryType, setParmaanDiscoveryType] = useState('similar')
  const [parmaanShabadCount, setParmaanShabadCount] = useState(5)
  const [shareStatus, setShareStatus] = useState('')
  const [copiedIndex, setCopiedIndex] = useState(null)
  const [shabadCount, setShabadCount] = useState(null)
  const [feedbackOpen, setFeedbackOpen] = useState(false)
  const [feedbackResponseContent, setFeedbackResponseContent] = useState('')

  const messagesEndRef = useRef(null)
  const baseUrl = apiBase()

  const fetchShabadCount = useCallback(async () => {
    try {
      const r = await fetch(`${baseUrl}/api/stats/knowledge`, { cache: 'no-store' })
      if (!r.ok) return
      const d = await r.json()
      if (typeof d.shabad_count === 'number') setShabadCount(d.shabad_count)
    } catch {
      /* ignore */
    }
  }, [baseUrl])

  useEffect(() => {
    fetchShabadCount()
    const id = setInterval(fetchShabadCount, 45_000)
    return () => clearInterval(id)
  }, [fetchShabadCount])

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === 'visible') fetchShabadCount()
    }
    document.addEventListener('visibilitychange', onVis)
    return () => document.removeEventListener('visibilitychange', onVis)
  }, [fetchShabadCount])

  const shabadCountLabel =
    shabadCount != null
      ? t('knowledgeShabadCount').replace('{count}', shabadCount.toLocaleString())
      : t('knowledgeShabadCount').replace('{count}', '—')

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

  const handleChatDeleted = useCallback(
    (deletedId) => {
      setChats((prev) => prev.filter((c) => c.id !== deletedId))
      if (activeChatId === deletedId) {
        setActiveChatId(null)
        setMessages([])
        setSuggestions([])
      }
    },
    [activeChatId]
  )

  const copyMessageText = async (text, index) => {
    try {
      await navigator.clipboard.writeText(text || '')
      setCopiedIndex(index)
      setTimeout(() => setCopiedIndex((i) => (i === index ? null : i)), 2000)
    } catch {
      /* ignore */
    }
  }

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

  const handleSend = async (query, options = {}) => {
    const { anchorShabadId } = options
    if (!token) {
      const msg =
        sessionStatus === 'unauthenticated'
          ? 'Sign in to send messages and receive answers.'
          : 'Your session is not connected to the server (missing API token). Open Settings for help, or sign out and sign in again.'
      setError(msg)
      return
    }
    setError('')
    setLoading(true)
    setSuggestions([])

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
        language,
        message_history: messageHistory.slice(-20),
        guidance_mode: guidanceMode,
      }
      if (guidanceMode === 'parmaan') {
        body.parmaan_discovery_type = parmaanDiscoveryType
        body.parmaan_shabad_count = parmaanShabadCount
      }
      if (anchorShabadId) body.anchor_shabad_id = anchorShabadId
      if (chatId) body.chat_id = chatId

      const askController = new AbortController()
      const askTimeout = setTimeout(() => askController.abort(), ASK_TIMEOUT_MS)
      let response
      try {
        response = await fetch(`${baseUrl}/ask`, {
          method: 'POST',
          headers,
          body: JSON.stringify(body),
          signal: askController.signal,
        })
      } finally {
        clearTimeout(askTimeout)
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        setMessages((prev) => {
          if (
            prev.length > 0 &&
            prev[prev.length - 1]?.role === 'user' &&
            prev[prev.length - 1]?.content === query
          ) {
            return prev.slice(0, -1)
          }
          return prev
        })
        if (errorData.code === 'birth_year_required') {
          router.push('/onboarding?callbackUrl=/chat')
          return
        }
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
          guidanceMode: data.guidance_mode,
          isDisambiguation: data.is_disambiguation === true,
          disambiguationCandidates: data.disambiguation_candidates || [],
          originalQuery: data.original_query || '',
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
      const aborted = err?.name === 'AbortError'
      setError(
        aborted
          ? 'The request took too long. Check your connection and API URL, then try again.'
          : err.message || 'Something went wrong. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion)
  }

  const handleDisambiguationSelect = (candidate) => {
    if (!candidate?.shabad_id || loading) return
    const gm = candidate.gurmukhi || ''
    const en = candidate.english_translation || ''
    const preview = gm ? truncateText(gm, 100) : truncateText(en, 80)
    const userLabel = preview ? `Selected: ${preview}` : `Selected shabad: ${candidate.shabad_id}`
    handleSend(userLabel, { anchorShabadId: candidate.shabad_id })
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
        token={token}
        onChatDeleted={handleChatDeleted}
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
            <span className="knowledge-count" title={t('knowledgeShabadCountTitle')}>
              {shabadCountLabel}
            </span>
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
          <div className="mobile-header-top">
            <button type="button" className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              ☰
            </button>
            <div className="mobile-header-logo">
              <Logo variant="compact" />
            </div>
          </div>
          <p className="mobile-knowledge-count" title={t('knowledgeShabadCountTitle')}>
            {shabadCountLabel}
          </p>
        </header>

        <section className="chat-messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              {error && (
                <div className="error-message error-message--prominent" role="alert">
                  {error}
                </div>
              )}
              <Logo />
              <h1>{t('appName')}</h1>
              <p>{t('tagline')}</p>
              <p className="persona-from-profile-hint">
                Response style follows your year of birth. Update it anytime in <Link href="/settings">Settings</Link>.
              </p>
            </div>
          ) : (
            <div className="messages-thread">
              {messages.map((msg, index) => (
                <div key={index} className={`message message--${msg.role}`}>
                  <div className="message-toolbar">
                    <div className="message-label">{msg.role === 'user' ? t('you') : t('guru')}</div>
                    <div className="message-toolbar-actions">
                      <button
                        type="button"
                        className="message-copy-btn"
                        onClick={() => copyMessageText(msg.content, index)}
                        aria-label={t('copyMessage')}
                      >
                        {copiedIndex === index ? t('copyMessageDone') : t('copyMessage')}
                      </button>
                      {msg.role === 'assistant' &&
                        !msg.isDisambiguation &&
                        typeof msg.content === 'string' &&
                        msg.content.trim() !== '' && (
                          <FeedbackButton
                            label={t('feedbackButton')}
                            disabled={loading}
                            onClick={() => {
                              setFeedbackResponseContent(msg.content)
                              setFeedbackOpen(true)
                            }}
                          />
                        )}
                    </div>
                  </div>
                  <div className="message-content">
                    <MarkdownRenderer content={msg.content} />
                    {msg.isDisambiguation && msg.disambiguationCandidates?.length > 0 && (
                      <div className="disambiguation-options" aria-label="Choose matching shabad">
                        {msg.disambiguationCandidates.map((c) => (
                          <button
                            key={c.shabad_id}
                            type="button"
                            className="disambiguation-btn"
                            disabled={loading}
                            onClick={() => handleDisambiguationSelect(c)}
                          >
                            {c.source ? (
                              <span className="disambiguation-meta">{c.source}</span>
                            ) : null}
                            <span className="disambiguation-gurmukhi gurmukhi-text">
                              {truncateText(c.gurmukhi || '', 160)}
                            </span>
                            {c.romanization ? (
                              <span className="disambiguation-roman">
                                {truncateText(c.romanization, 100)}
                              </span>
                            ) : null}
                          </button>
                        ))}
                      </div>
                    )}
                    {msg.shabad?.sttm_link &&
                    !contentHasParmaanVerbatimBlocks(msg.content) &&
                    msg.guidanceMode !== 'parmaan' ? (
                      <a
                        href={msg.shabad.sttm_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="sttm-link"
                      >
                        View on SikhiToTheMax ↗
                      </a>
                    ) : null}
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
            {!token && sessionStatus !== 'loading' && (
              <p className="chat-auth-hint" role="status">
                {sessionStatus === 'unauthenticated' ? (
                  <>
                    {t('signInToSave')}{' '}
                    <Link href="/login?callbackUrl=/chat" className="chat-auth-hint-link">
                      {t('signIn')}
                    </Link>
                  </>
                ) : (
                  <>
                    Account not fully linked to the server — open{' '}
                    <Link href="/settings" className="chat-auth-hint-link">
                      Settings
                    </Link>{' '}
                    or sign out and sign in again.
                  </>
                )}
              </p>
            )}
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
            {guidanceMode === 'parmaan' && (
              <ParmaanDiscoveryBar
                discoveryType={parmaanDiscoveryType}
                onDiscoveryTypeChange={setParmaanDiscoveryType}
                shabadCount={parmaanShabadCount}
                onShabadCountChange={setParmaanShabadCount}
                disabled={loading}
              />
            )}
            <ChatInput
              onSend={handleSend}
              disabled={loading}
              loading={loading}
              placeholder={guidanceMode === 'parmaan' ? t('parmaanMessagePlaceholder') : undefined}
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

        <FeedbackModal
          open={feedbackOpen}
          onClose={() => setFeedbackOpen(false)}
          responseContent={feedbackResponseContent}
          chatId={activeChatId}
          token={token}
          baseUrl={baseUrl}
          t={t}
        />
      </main>
    </div>
  )
}
