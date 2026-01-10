import React from 'react'
import './LandingPage.css'

function LandingPage({ onStart }) {
  return (
    <div className="landing-page">
      <div className="landing-container">
        <h1 className="landing-title">Startup Idea Validator</h1>
        <p className="landing-subtitle">
          Get instant feedback on your startup idea through our AI-assisted analysis
        </p>
        <p className="landing-description">
          Our system analyzes three key areas:
        </p>
        <ul className="landing-features">
          <li>📊 <strong>Problem Reality</strong> - How real and severe is the problem?</li>
          <li>🏢 <strong>Market Reality</strong> - What's the competitive landscape?</li>
          <li>⚡ <strong>Leverage Reality</strong> - Does your solution have true leverage?</li>
        </ul>
        <button className="start-button" onClick={onStart}>
          Start Analysis
        </button>
      </div>
    </div>
  )
}

export default LandingPage
