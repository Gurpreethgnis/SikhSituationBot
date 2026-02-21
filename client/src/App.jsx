import React from 'react';
import './index.css';

function App() {
    return (
        <div className="app-container">
            <div className="glass-card">
                <div className="icon-container">🪯</div>
                <h1 className="title">Hello <span className="highlight">SikhSituationBot</span></h1>
                <p className="subtitle">Your Gurbani-based guidance awaits.</p>
                <button className="primary-btn">Begin Journey</button>
            </div>
        </div>
    );
}

export default App;
