import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Header from './Header'

const CatalogHeader = ({ stats }) => {
  const [animatedStats, setAnimatedStats] = useState({
    projects: 0,
    datasets: 0,
    usecases: 0,
    countries: 0
  })
  const isInitialLoad = useRef(true)
  const prevStats = useRef(null)

  // Animate counters - fast on filter, slow on initial load
  useEffect(() => {
    if (!stats) return

    // Use fast animation for filter changes, slow for initial load
    const duration = isInitialLoad.current ? 1500 : 300 // 1.5s initial, 300ms for filters
    const steps = isInitialLoad.current ? 60 : 15
    const interval = duration / steps

    // Get starting values (animate from previous values, not 0)
    const startValues = prevStats.current || { 
      total_projects: 0, 
      total_datasets: 0, 
      total_usecases: 0, 
      total_countries: 0 
    }

    let step = 0
    const timer = setInterval(() => {
      step++
      const progress = step / steps

      // Interpolate from previous values to new values
      setAnimatedStats({
        projects: Math.floor(startValues.total_projects + (stats.total_projects - startValues.total_projects) * progress),
        datasets: Math.floor(startValues.total_datasets + (stats.total_datasets - startValues.total_datasets) * progress),
        usecases: Math.floor(startValues.total_usecases + (stats.total_usecases - startValues.total_usecases) * progress),
        countries: Math.floor(startValues.total_countries + (stats.total_countries - startValues.total_countries) * progress)
      })

      if (step >= steps) {
        clearInterval(timer)
        setAnimatedStats({
          projects: stats.total_projects,
          datasets: stats.total_datasets,
          usecases: stats.total_usecases,
          countries: stats.total_countries
        })
        // Store current stats for next animation
        prevStats.current = stats
        isInitialLoad.current = false
      }
    }, interval)

    return () => clearInterval(timer)
  }, [stats])

  if (!stats) return null

  return (
    <header>
      <Header />
      <div className="header-content">
        <div className="header-main">
          <div className="header-text">
            <h1>Fair Forward - Open Data & Use Cases</h1>
            <p className="subtitle">
              Exploring datasets and solutions for global challenges across agriculture, 
              language technology, climate action, energy, and more.
            </p>
            <a 
              href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="header-learn-more"
            >
              [Learn more about Fair Forward]
            </a>
          </div>
          
          <div className="header-stats">
            <div className="stat-meta-row">
              <div className="stat-item stat-meta">
                <div className="stat-text">
                  <div className="stat-value">{animatedStats.projects}</div>
                  <div className="stat-label">Projects</div>
                </div>
              </div>
              
              {/* Insights Preview Card */}
              <Link to="/insights" className="insights-preview-card" title="Explore Insights & Visualizations">
              <div className="insights-preview-graphics">
                {/* Mini World Map */}
                {/* <div className="mini-viz mini-map">
                  <svg viewBox="0 0 60 30" className="mini-map-svg">
                    <ellipse cx="30" cy="15" rx="28" ry="13" fill="#e2e8f0" />
                    <circle cx="20" cy="12" r="3" fill="#059669" opacity="0.8" />
                    <circle cx="35" cy="10" r="2" fill="#059669" opacity="0.6" />
                    <circle cx="28" cy="18" r="2.5" fill="#059669" opacity="0.7" />
                    <circle cx="42" cy="14" r="1.5" fill="#059669" opacity="0.5" />
                    <circle cx="15" cy="16" r="2" fill="#059669" opacity="0.6" />
                  </svg>
                </div> */}
                
                {/* Mini SDG Bars */}
                <div className="mini-viz mini-bars">
                  <div className="mini-bar" style={{ height: '80%', background: '#E5243B' }}></div>
                  <div className="mini-bar" style={{ height: '60%', background: '#DDA63A' }}></div>
                  <div className="mini-bar" style={{ height: '90%', background: '#4C9F38' }}></div>
                  <div className="mini-bar" style={{ height: '45%', background: '#26BDE2' }}></div>
                  <div className="mini-bar" style={{ height: '70%', background: '#FCC30B' }}></div>
                </div>
                
                {/* Mini Network Bubbles*/}
                <div className="mini-viz mini-network">
                  <div className="mini-bubble" style={{ width: '18px', height: '18px', background: '#2563eb' }}></div>
                  <div className="mini-bubble" style={{ width: '14px', height: '14px', background: '#6366f1' }}></div>
                  <div className="mini-bubble" style={{ width: '10px', height: '10px', background: '#059669' }}></div>
                  <div className="mini-bubble" style={{ width: '12px', height: '12px', background: '#059669' }}></div>
                </div> 
              </div>
              <div className="insights-preview-text">
                <span className="insights-preview-title">            
                  Insights
                </span>
                <span className="insights-preview-desc">Explore maps, charts & partner networks</span>
              </div>
              <i className="fas fa-arrow-right insights-preview-arrow"></i>
              </Link>
            </div>
            
            <div className="stats-parallelogram">
              <div className="stat-item">
                <div className="stat-text">
                  <div className="stat-value">{animatedStats.datasets}</div>
                  <div className="stat-label">Datasets</div>
                </div>
              </div>
              <div className="stat-item">
                <div className="stat-text">
                  <div className="stat-value">{animatedStats.usecases}</div>
                  <div className="stat-label">Use Cases</div>
                </div>
              </div>
              <div className="stat-item">
                <div className="stat-text">
                  <div className="stat-value">{animatedStats.countries}</div>
                  <div className="stat-label">Countries</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default CatalogHeader

