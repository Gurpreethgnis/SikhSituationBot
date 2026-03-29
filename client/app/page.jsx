'use client'

import React, { useState, useEffect, useRef } from 'react'
import ChatInput from './components/ChatInput.jsx'
import Perspectives from './components/Perspectives.jsx'
import Logo from './components/Logo'
import Sidebar from './components/Sidebar.jsx'
import MarkdownRenderer from './components/MarkdownRenderer'
import './App.css'

function App() {
  const [persona, setPersona] = useState('adult')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [history, setHistory] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  const messagesEndRef = useRef(null)

  // Scroll to bottom whenever messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  // Load history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('sikh_bot_history')
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory))
      } catch (e) {
        console.error('Failed to parse history', e)
      }
    }
  }, [])

  // Save history to localStorage
  const saveToHistory = (query) => {
    const newHistoryItem = { 
      title: query.length > 30 ? query.substring(0, 30) + '...' : query,
      query: query,
      timestamp: new Date().toISOString()
    }
    const updatedHistory = [newHistoryItem, ...history.filter(h => h.query !== query)].slice(0, 20)
    setHistory(updatedHistory)
    localStorage.setItem('sikh_bot_history', JSON.stringify(updatedHistory))
  }

  const handleSend = async (query) => {
    setError('')
    setLoading(true)
    
    // Add user message to thread
    const userMessage = { role: 'user', content: query }
    setMessages(prev => [...prev, userMessage])
    saveToHistory(query)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
      const endpoint = `${baseUrl}/ask`
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, persona }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Failed to fetch guidance: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
      } else {
        let content = data.response
        let extractedSuggestions = []
        
        if (content.includes('[SUGGESTIONS]')) {
          const parts = content.split('[SUGGESTIONS]')
          content = parts[0].trim()
          const suggestionLines = parts[1].trim().split('\n')
          extractedSuggestions = suggestionLines
            .map(s => s.replace(/^- /, '').trim())
            .filter(s => s.length > 0)
        }

        const aiMessage = { 
          role: 'assistant', 
          content: content,
          shabad: data.shabad,
          persona: data.persona,
          isQuestion: data.is_clarification === true
        }
        setMessages(prev => [...prev, aiMessage])
        setSuggestions(extractedSuggestions)
      }
    } catch (err) {
      console.error('Chat error:', err)
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setSuggestions([])
    setError('')
  }

  const handleSelectHistory = (historyItem) => {
    setMessages([])
    setSuggestions([])
    handleSend(historyItem.query)
  }

  const handleSuggestionClick = (suggestion) => {
    handleSend(suggestion)
  }

  return (
    <div className="app-container">
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`} 
        onClick={() => setSidebarOpen(false)}
      />
      <Sidebar 
        history={history} 
        onSelectHistory={handleSelectHistory} 
        onNewChat={handleNewChat}
        isOpen={sidebarOpen}
      />
      
      <main className="chat-main">
        <header className="mobile-header">
          <button 
            className="menu-toggle" 
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>
          <div className="mobile-logo">☬</div>
        </header>

        <section className="chat-messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <Logo />
              <h1>SikhSituationBot</h1>
              <p>Seek guidance from the Guru Granth Sahib for your life situations.</p>
              <Perspectives activePersona={persona} onPersonaChange={setPersona} />
            </div>
          ) : (
            <div className="messages-thread">
              {messages.map((msg, index) => (
                <div key={index} className={`message message--${msg.role}`}>
                  <div className="message-label">
                    {msg.role === 'user' ? 'You' : 'Guru'}
                  </div>
                  <div className="message-content">
                    <MarkdownRenderer content={msg.content} />
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="message message--assistant loading">
                  <div className="message-label">Seeking Wisdom...</div>
                  <div className="message-content">
                    <div className="typing-dots"><span></span><span></span><span></span></div>
                  </div>
                </div>
              )}
              {error && <div className="error-message">{error}</div>}
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
                    className="suggestion-chip"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            <ChatInput onSend={handleSend} disabled={loading} />
            <p className="footer-disclaimer">
              SikhSituationBot provides spiritual perspectives, not professional advice.
            </p>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App
