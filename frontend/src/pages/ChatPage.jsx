import React, { useState, useEffect, useRef } from 'react'
import './ChatPage.css'

const API_BASE = 'http://localhost:8000'

function ChatPage({ onComplete, onBack }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // Start intake session when component mounts
    startIntake()
  }, [])

  const startIntake = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/intake/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initial_text: null })
      })
      
      if (!response.ok) {
        throw new Error('Failed to start intake')
      }

      const data = await response.json()
      setSessionId(data.session_id)
      
      // Add first question as system message
      setMessages([{
        role: 'system',
        content: data.question,
        field: data.field
      }])
    } catch (err) {
      setError('Failed to start intake. Please try again.')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!inputValue.trim() || isLoading || !sessionId) {
      return
    }

    const userMessage = inputValue.trim()
    setInputValue('')
    
    // Add user message immediately
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage
    }])

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/intake/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          answer: userMessage
        })
      })

      if (!response.ok) {
        throw new Error('Failed to process answer')
      }

      const data = await response.json()

      if (data.error) {
        // Validation error - show error message and same question again
        setMessages(prev => [...prev, {
          role: 'system',
          content: `${data.error}\n\n${data.question}`,
          field: data.field,
          isError: true
        }])
      } else if (data.complete) {
        // Intake complete - run analysis
        setMessages(prev => [...prev, {
          role: 'system',
          content: 'Great! I have all the information I need. Analyzing your startup idea...'
        }])
        
        // Run analysis
        await runAnalysis()
      } else {
        // Next question
        setMessages(prev => [...prev, {
          role: 'system',
          content: data.question,
          field: data.field
        }])
      }
    } catch (err) {
      setError('Failed to send message. Please try again.')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const runAnalysis = async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      })

      if (!response.ok) {
        throw new Error('Analysis failed')
      }

      const data = await response.json()
      onComplete(data)
    } catch (err) {
      setError('Analysis failed. Please try again.')
      console.error(err)
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <button className="back-button" onClick={onBack}>← Back</button>
        <h2>Startup Idea Analysis</h2>
        <div></div>
      </div>

      <div className="chat-container">
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message ${msg.role === 'user' ? 'message-user' : 'message-system'} ${msg.isError ? 'message-error' : ''}`}
            >
              <div className="message-bubble">
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message message-system">
              <div className="message-bubble loading-bubble">
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={handleSubmit} className="input-form">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your answer..."
              className="message-input"
              disabled={isLoading || !sessionId}
            />
            <button
              type="submit"
              className="send-button"
              disabled={isLoading || !inputValue.trim() || !sessionId}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
