import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/Header'
import WorldMap from '../components/WorldMap'

const InsightsPage = () => {
  const [insightsData, setInsightsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Fetch insights data
    fetch('./data/insights.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load insights data')
        return res.json()
      })
      .then(data => {
        setInsightsData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading insights:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div>
        <Header />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '4rem' }}>
            <p>Loading insights...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !insightsData) {
    return (
      <div>
        <Header />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-light)' }}>
            <p>Unable to load insights data. Please run the build script.</p>
            <p style={{ fontSize: '0.9rem', marginTop: '1rem' }}>
              Error: {error || 'No data available'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const { total_projects, total_countries, map_data } = insightsData

  return (
    <div>
      <Header />
      
      <div className="container">
        <Link to="/" className="back-link">
          <i className="fas fa-arrow-left"></i>
          Back to Catalog
        </Link>

        <div className="page-header">
          <h1>Insights and Visualisations</h1>
          <p>Explore the geographic distribution and reach of our project portfolio</p>
        </div>

        <div className="insight-card">
          <h2>
            <i className="fas fa-globe-africa"></i>
            Geographic Distribution
          </h2>
          <p>Interactive world map showing project distribution across {total_countries} countries</p>
          
          <div className="insight-summary">
            <div className="insight-summary-item">
              <div className="label">Total Projects</div>
              <div className="value">{total_projects}</div>
            </div>
            <div className="insight-summary-item">
              <div className="label">Countries Reached</div>
              <div className="value">{total_countries}</div>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem' }}>
            <WorldMap projectData={map_data} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default InsightsPage

