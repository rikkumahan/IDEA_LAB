import React, { useState } from 'react'
import LandingPage from './pages/LandingPage'
import ChatPage from './pages/ChatPage'
import ResultsPage from './pages/ResultsPage'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('landing')
  const [results, setResults] = useState(null)

  const navigateTo = (page, data = null) => {
    setCurrentPage(page)
    if (data) {
      setResults(data)
    }
  }

  return (
    <div className="app">
      {currentPage === 'landing' && (
        <LandingPage onStart={() => navigateTo('chat')} />
      )}
      {currentPage === 'chat' && (
        <ChatPage
          onComplete={(resultData) => navigateTo('results', resultData)}
          onBack={() => navigateTo('landing')}
        />
      )}
      {currentPage === 'results' && (
        <ResultsPage
          results={results}
          onStartNew={() => navigateTo('landing')}
        />
      )}
    </div>
  )
}

export default App
