import React from 'react'
import './ResultsPage.css'

function ResultsPage({ results, onStartNew }) {
  if (!results || !results.validation_result) {
    return (
      <div className="results-page">
        <div className="results-container">
          <h2>No Results</h2>
          <p>Something went wrong. Please try again.</p>
          <button className="new-analysis-button" onClick={onStartNew}>
            Start New Analysis
          </button>
        </div>
      </div>
    )
  }

  const { validation_result, explanation } = results
  const { problem_reality, market_reality, leverage_reality, validation_state } = validation_result

  const getBadgeClass = (level) => {
    const mapping = {
      'DRASTIC': 'badge-critical',
      'SEVERE': 'badge-high',
      'MODERATE': 'badge-medium',
      'LOW': 'badge-low',
      'HIGH': 'badge-high',
      'MEDIUM': 'badge-medium',
      'NONE': 'badge-low',
      'PRESENT': 'badge-high',
      'REAL': 'badge-high',
      'WEAK': 'badge-low',
      'STRONG_FOUNDATION': 'badge-critical',
      'REAL_PROBLEM_WEAK_EDGE': 'badge-medium',
      'WEAK_FOUNDATION': 'badge-low'
    }
    return mapping[level] || 'badge-default'
  }

  return (
    <div className="results-page">
      <div className="results-container">
        <h1 className="results-title">Analysis Results</h1>

        {/* Validation Summary */}
        <div className="section validation-summary">
          <h2>Validation Summary</h2>
          <div className="validation-class">
            <span className={`badge ${getBadgeClass(validation_state.validation_class)}`}>
              {validation_state.validation_class.replace(/_/g, ' ')}
            </span>
          </div>
          {explanation && (
            <div className="explanation">
              <p>{explanation}</p>
            </div>
          )}
        </div>

        {/* 1. Problem Reality */}
        <div className="section">
          <h2>1️⃣ Problem Reality</h2>
          <div className="section-content">
            <div className="metric">
              <span className="metric-label">Problem Level:</span>
              <span className={`badge ${getBadgeClass(problem_reality.problem_level)}`}>
                {problem_reality.problem_level}
              </span>
            </div>
            {problem_reality.signals && (
              <div className="signals">
                <h4>Signals Detected:</h4>
                <div className="signal-grid">
                  <div className="signal-item">
                    <span className="signal-label">Complaints:</span>
                    <span className={`badge ${getBadgeClass(problem_reality.signals.complaint_level)}`}>
                      {problem_reality.signals.complaint_level}
                    </span>
                  </div>
                  <div className="signal-item">
                    <span className="signal-label">Workarounds:</span>
                    <span className={`badge ${getBadgeClass(problem_reality.signals.workaround_level)}`}>
                      {problem_reality.signals.workaround_level}
                    </span>
                  </div>
                  <div className="signal-item">
                    <span className="signal-label">Intensity:</span>
                    <span className={`badge ${getBadgeClass(problem_reality.signals.intensity_level)}`}>
                      {problem_reality.signals.intensity_level}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 2. Market Reality */}
        <div className="section">
          <h2>2️⃣ Market Reality</h2>
          <div className="section-content">
            {market_reality.market_strength && (
              <div className="market-metrics">
                <div className="metric">
                  <span className="metric-label">Competitor Density:</span>
                  <span className={`badge ${getBadgeClass(market_reality.market_strength.competitor_density)}`}>
                    {market_reality.market_strength.competitor_density}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Market Fragmentation:</span>
                  <span className="badge badge-default">
                    {market_reality.market_strength.market_fragmentation}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Solution Maturity:</span>
                  <span className="badge badge-default">
                    {market_reality.market_strength.solution_class_maturity}
                  </span>
                </div>
              </div>
            )}
            {market_reality.market_strength?.market_risk && market_reality.market_strength.market_risk.length > 0 && (
              <div className="risk-flags">
                <h4>Market Risks:</h4>
                <ul>
                  {market_reality.market_strength.market_risk.map((risk, idx) => (
                    <li key={idx} className="risk-item">{risk.replace(/_/g, ' ')}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* 3. Leverage Reality */}
        <div className="section">
          <h2>3️⃣ Leverage Reality</h2>
          <div className="section-content">
            <div className="metric">
              <span className="metric-label">Leverage Presence:</span>
              <span className={`badge ${getBadgeClass(validation_state.leverage_presence)}`}>
                {validation_state.leverage_presence}
              </span>
            </div>
            {leverage_reality.leverage_flags && leverage_reality.leverage_flags.length > 0 && (
              <div className="leverage-flags">
                <h4>Leverage Flags:</h4>
                <div className="flag-grid">
                  {leverage_reality.leverage_flags.map((flag, idx) => (
                    <span key={idx} className="flag-badge">
                      {flag.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <button className="new-analysis-button" onClick={onStartNew}>
          Start New Analysis
        </button>
      </div>
    </div>
  )
}

export default ResultsPage
