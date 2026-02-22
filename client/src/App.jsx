import ChatInput from './components/ChatInput.jsx'

function App() {
  const handleSend = (query) => {
    console.log('Query:', query)
    // TODO: Wire to backend / display results (task 3: chat flow)
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">SikhSituationBot</h1>
        <p className="app__tagline">Gurbani-based guidance for life's moments</p>
      </header>
      <main className="app__main">
        <ChatInput onSend={handleSend} placeholder="Share how you're feeling or ask for guidance..." />
      </main>
    </div>
  )
}

export default App
