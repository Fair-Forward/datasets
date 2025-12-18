import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Header from '../components/Header'
import WorldMap from '../components/WorldMap'
import SDGChart from '../components/SDGChart'
import MaturityChart from '../components/MaturityChart'
import { withBasePath } from '../utils/basePath'

const InsightsPage = () => {
  const [insightsData, setInsightsData] = useState(null)
  const [catalogData, setCatalogData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState(null)

  useEffect(() => {
    // Fetch both insights and catalog data
    Promise.all([
      fetch(withBasePath('data/insights.json')).then(res => {
        if (!res.ok) throw new Error('Failed to load insights data')
        return res.json()
      }),
      fetch(withBasePath('data/catalog.json')).then(res => {
        if (!res.ok) throw new Error('Failed to load catalog data')
        return res.json()
      })
    ])
      .then(([insights, catalog]) => {
        setInsightsData(insights)
        setCatalogData(catalog)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading data:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const handleCountryClick = (countryData) => {
    setSelectedCountry(countryData)
  }

  const handleSDGClick = (sdgData) => {
    window.location.href = withBasePath(`?sdg=${encodeURIComponent(sdgData.sdg)}`)
  }

  // Calculate maturity distribution from catalog data
  const getMaturityDistribution = () => {
    if (!catalogData?.projects) return null
    
    const maturityCounts = {}
    catalogData.projects.forEach(project => {
      const maturity = project.maturity?.trim() || 'Not specified'
      if (maturity && maturity !== '') {
        maturityCounts[maturity] = (maturityCounts[maturity] || 0) + 1
      }
    })
    
    // Only return if we have actual data
    const totalWithMaturity = Object.values(maturityCounts).reduce((a, b) => a + b, 0)
    return totalWithMaturity > 0 ? maturityCounts : null
  }

  if (loading) {
    return (
      <div className="insights-page">
        <Header />
        <div className="container">
          <div className="insights-loading">
            <div className="insights-loading-spinner"></div>
            <p>Loading insights...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !insightsData) {
    return (
      <div className="insights-page">
        <Header />
        <div className="container">
          <div className="insights-error">
            <i className="fas fa-exclamation-triangle"></i>
            <p>Unable to load insights data. Please run the build script.</p>
            <span>Error: {error || 'No data available'}</span>
          </div>
        </div>
      </div>
    )
  }

  const { total_projects, total_countries, map_data, sdg_distribution } = insightsData
  const maturityDistribution = getMaturityDistribution()

  return (
    <div className="insights-page">
      <Header />
      
      <div className="container">
        <Link to="/" className="back-link">
          <i className="fas fa-arrow-left"></i>
          Back to Catalog
        </Link>

        <div className="page-header">
          <h1>Insights & Visualisations</h1>
          <p className="page-header-subtitle">
            Explore the distribution, coverage, and characteristics of projects in our catalog
          </p>
        </div>

        {/* Summary Stats */}
        <div className="insights-hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-icon">
              <i className="fas fa-database"></i>
            </div>
            <div className="hero-stat-content">
              <span className="hero-stat-value">{total_projects}</span>
              <span className="hero-stat-label">Total Projects</span>
            </div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-icon">
              <i className="fas fa-globe-africa"></i>
            </div>
            <div className="hero-stat-content">
              <span className="hero-stat-value">{total_countries}</span>
              <span className="hero-stat-label">Countries</span>
            </div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-icon">
              <i className="fas fa-bullseye"></i>
            </div>
            <div className="hero-stat-content">
              <span className="hero-stat-value">{Object.keys(sdg_distribution || {}).length}</span>
              <span className="hero-stat-label">SDGs Covered</span>
            </div>
          </div>
        </div>

        {/* World Map Section */}
        <div className="insight-card insight-card-map">
          <div className="insight-card-header">
            <div>
              <h2>
                <i className="fas fa-globe-africa"></i>
                Geographic Distribution
              </h2>
              <p>Click on highlighted regions to explore projects</p>
            </div>
          </div>

          <div className="map-container">
            <WorldMap 
              projectData={map_data} 
              onCountryClick={handleCountryClick}
              selectedCountry={selectedCountry}
            />
            
            {selectedCountry && (
              <div className="country-detail-panel">
                <button 
                  className="country-detail-close" 
                  onClick={() => setSelectedCountry(null)}
                  aria-label="Close panel"
                >
                  <i className="fas fa-times"></i>
                </button>
                <div className="country-detail-header">
                  <h3>{selectedCountry.name}</h3>
                  <div className="country-project-count">
                    <span className="country-count-value">{selectedCountry.projects}</span>
                    <span className="country-count-label">project{selectedCountry.projects !== 1 ? 's' : ''}</span>
                  </div>
                </div>
                
                {selectedCountry.sdgs?.length > 0 && (
                  <div className="country-detail-section">
                    <h4>
                      <i className="fas fa-bullseye"></i>
                      SDGs Addressed
                    </h4>
                    <div className="country-sdg-badges">
                      {selectedCountry.sdgs.map(sdg => {
                        const num = sdg.replace('SDG ', '')
                        return (
                          <span key={sdg} className="country-sdg-badge">
                            <img 
                              src={withBasePath(`img/sdg-${num}.png`)} 
                              alt=""
                              className="country-sdg-mini-icon"
                              onError={(e) => { e.target.style.display = 'none' }}
                            />
                            {sdg}
                          </span>
                        )
                      })}
                    </div>
                  </div>
                )}
                
                {selectedCountry.data_types?.length > 0 && (
                  <div className="country-detail-section">
                    <h4>
                      <i className="fas fa-database"></i>
                      Data Types
                    </h4>
                    <div className="country-data-types">
                      {selectedCountry.data_types.map(dt => (
                        <span key={dt} className="country-data-type">{dt}</span>
                      ))}
                    </div>
                  </div>
                )}
                
                <Link 
                  to={`/?region=${encodeURIComponent(selectedCountry.name)}`}
                  className="country-view-projects"
                >
                  <span>View all projects</span>
                  <i className="fas fa-arrow-right"></i>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Maturity / Pipeline Status Section */}
        {catalogData?.projects && (
          <div className="insight-card insight-card-maturity">
            <div className="insight-card-header">
              <div>
                <h2>
                  <i className="fas fa-layer-group"></i>
                  Project Maturity
                </h2>
                <p>How projects progress from data to deployment</p>
              </div>
            </div>
            
            <MaturityChart 
              maturityDistribution={maturityDistribution} 
              catalogProjects={catalogData.projects}
            />
          </div>
        )}

        {/* SDG Distribution Section */}
        {sdg_distribution && Object.keys(sdg_distribution).length > 0 && (
          <div className="insight-card insight-card-sdg">
            <div className="insight-card-header">
              <div>
                <h2>
                  <i className="fas fa-bullseye"></i>
                  SDG Alignment
                </h2>
                <p>Distribution of projects across Sustainable Development Goals</p>
              </div>
            </div>
            
            <SDGChart 
              sdgDistribution={sdg_distribution}
              onSDGClick={handleSDGClick}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default InsightsPage
