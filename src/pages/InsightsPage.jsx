import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/Header'
import WorldMap from '../components/WorldMap'
import { withBasePath } from '../utils/basePath'

const InsightsPage = () => {
  const [insightsData, setInsightsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState(null)

  useEffect(() => {
    // Fetch insights data
    fetch(withBasePath('data/insights.json'))
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

  const handleCountryClick = (countryData) => {
    setSelectedCountry(countryData)
  }

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

  const { total_projects, total_countries, map_data, sdg_distribution } = insightsData

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
        </div>

        <div className="insight-card">
          <div className="insight-card-header">
            <div>
              <h2>
                <i className="fas fa-globe-africa"></i>
                Geographic Distribution
              </h2>
              <p>Click on any highlighted country to see details</p>
            </div>
            <div className="insight-stats-compact">
              <div className="stat-compact">
                <span className="stat-value-compact">{total_projects}</span>
                <span className="stat-label-compact">Projects</span>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-compact">
                <span className="stat-value-compact">{total_countries}</span>
                <span className="stat-label-compact">Countries</span>
              </div>
            </div>
          </div>

          <div className="map-container">
            <WorldMap 
              projectData={map_data} 
              onCountryClick={handleCountryClick}
            />
            
            {selectedCountry && (
              <div className="country-detail-panel">
                <button 
                  className="country-detail-close" 
                  onClick={() => setSelectedCountry(null)}
                >
                  <i className="fas fa-times"></i>
                </button>
                <h3>{selectedCountry.name}</h3>
                <div className="country-stat">
                  <i className="fas fa-folder-open"></i>
                  <span>{selectedCountry.projects} project{selectedCountry.projects !== 1 ? 's' : ''}</span>
                </div>
                {selectedCountry.sdgs?.length > 0 && (
                  <div className="country-detail-section">
                    <h4>SDGs Addressed</h4>
                    <div className="country-sdg-badges">
                      {selectedCountry.sdgs.map(sdg => (
                        <span key={sdg} className="country-sdg-badge">{sdg}</span>
                      ))}
                    </div>
                  </div>
                )}
                {selectedCountry.data_types?.length > 0 && (
                  <div className="country-detail-section">
                    <h4>Data Types</h4>
                    <div className="country-data-types">
                      {selectedCountry.data_types.map(dt => (
                        <span key={dt} className="country-data-type">{dt}</span>
                      ))}
                    </div>
                  </div>
                )}
                <Link 
                  to={`/?country=${encodeURIComponent(selectedCountry.name)}`}
                  className="country-view-projects"
                >
                  View all projects in {selectedCountry.name}
                  <i className="fas fa-arrow-right"></i>
                </Link>
              </div>
            )}
          </div>
        </div>

        {sdg_distribution && Object.keys(sdg_distribution).length > 0 && (
          <div className="insight-card">
            <h2>
              <i className="fas fa-bullseye"></i>
              SDG Coverage
            </h2>
            <p>Distribution of projects across Sustainable Development Goals</p>
            <div className="sdg-grid">
              {Object.entries(sdg_distribution).map(([sdg, count]) => {
                const sdgNum = sdg.replace('SDG ', '')
                return (
                  <div key={sdg} className="sdg-item">
                    <img 
                      src={withBasePath(`img/sdg-${sdgNum}.png`)} 
                      alt={sdg}
                      className="sdg-icon-img"
                      onError={(e) => { e.target.style.display = 'none' }}
                    />
                    <div className="sdg-info">
                      <span className="sdg-name">{sdg}</span>
                      <span className="sdg-count">{count} project{count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default InsightsPage

