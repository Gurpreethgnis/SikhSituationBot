'use client'

import React from 'react'
import './Sidebar.css'

function Sidebar({ history, onSelectHistory, onNewChat }) {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <span className="plus-icon">+</span> New Chat
        </button>
      </div>
      
      <div className="sidebar__history">
        <h3 className="history-label">Recent Queries</h3>
        <div className="history-list">
          {history.length === 0 ? (
            <p className="no-history">No past queries yet.</p>
          ) : (
            history.map((item, index) => (
              <button 
                key={index} 
                className="history-item" 
                onClick={() => onSelectHistory(item)}
              >
                <span className="chat-icon">💬</span>
                <span className="history-text">{item.title}</span>
              </button>
            ))
          )}
        </div>
      </div>
      
      <div className="sidebar__footer">
        <div className="user-profile">
          <div className="user-avatar">GS</div>
          <span className="user-name">Gurbani Seeker</span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
