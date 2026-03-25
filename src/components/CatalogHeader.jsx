import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Header from './Header'

const CatalogHeader = ({ stats }) => {
  const [animatedStats, setAnimatedStats] = useState({
    projects: 0,
    datasets: 0,
    usecases: 0,
    accessNote: 0,
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
      total_access_note_projects: 0,
      total_countries: 0 
    }

    let step = 0
    const timer = setInterval(() => {
      step++
      const progress = step / steps

      // Interpolate from previous values to new values
      const prevAccess = startValues.total_access_note_projects ?? 0
      const nextAccess = stats.total_access_note_projects ?? 0
      setAnimatedStats({
        projects: Math.floor(startValues.total_projects + (stats.total_projects - startValues.total_projects) * progress),
        datasets: Math.floor(startValues.total_datasets + (stats.total_datasets - startValues.total_datasets) * progress),
        usecases: Math.floor(startValues.total_usecases + (stats.total_usecases - startValues.total_usecases) * progress),
        accessNote: Math.floor(prevAccess + (nextAccess - prevAccess) * progress),
        countries: Math.floor(startValues.total_countries + (stats.total_countries - startValues.total_countries) * progress)
      })

      if (step >= steps) {
        clearInterval(timer)
        setAnimatedStats({
          projects: stats.total_projects,
          datasets: stats.total_datasets,
          usecases: stats.total_usecases,
          accessNote: stats.total_access_note_projects ?? 0,
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
            <div className="stat-hero">
              <div className="stat-hero-value">{animatedStats.projects}</div>
              <div className="stat-hero-label">Projects</div>
            </div>
            <div className="stat-secondary-row">
              <div className="stat-secondary">
                <div className="stat-secondary-value">{animatedStats.datasets}</div>
                <div className="stat-secondary-label">Datasets</div>
              </div>
              <div className="stat-secondary-divider"></div>
              <div className="stat-secondary">
                <div className="stat-secondary-value">{animatedStats.usecases}</div>
                <div className="stat-secondary-label">Use Cases</div>
              </div>
              <div className="stat-secondary-divider"></div>
              <div className="stat-secondary">
                <div className="stat-secondary-value">{animatedStats.countries}</div>
                <div className="stat-secondary-label">Countries</div>
              </div>
            </div>
            <Link to="/insights" className="insights-link">
              Explore Insights & Visualizations <i className="fas fa-arrow-right"></i>
            </Link>
          </div>
        </div>
      </div>
    </header>
  )
}

export default CatalogHeader

