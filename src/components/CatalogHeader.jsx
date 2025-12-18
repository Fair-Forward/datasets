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
              <Link to="/insights" className="insights-link" title="View analytics">
                <i className="fas fa-chart-line"></i>
                <span>Insights &amp; visualisations</span>
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

