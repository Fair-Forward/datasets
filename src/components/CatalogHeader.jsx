import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Header from './Header'

const CatalogHeader = ({ stats, search, onSearchChange }) => {
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

    // On filter/search changes, snap the counters straight to the new values so they
    // don't re-animate (and flicker) under the search box on every keystroke.
    if (!isInitialLoad.current) {
      setAnimatedStats({
        projects: stats.total_projects,
        datasets: stats.total_datasets,
        usecases: stats.total_usecases,
        accessNote: stats.total_access_note_projects ?? 0,
        countries: stats.total_countries
      })
      prevStats.current = stats
      return
    }

    // First load animates the counters up from zero.
    const duration = 1500
    const steps = 60
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

  return (
    <header>
      <Header />
      <div className="header-content">
        <div className="hero">
          <h1>Fair Forward - Open Data &amp; Use Cases</h1>
          <p className="subtitle">
            Exploring datasets and solutions for global challenges across agriculture,
            language technology, climate action, energy, and more — built by our partners.
          </p>

          <div className="hero-search">
            <i className="fas fa-magnifying-glass" aria-hidden="true"></i>
            <input
              type="text"
              className="hero-search-input"
              placeholder="Search datasets and use cases"
              value={search || ''}
              onChange={(e) => onSearchChange?.(e.target.value)}
              aria-label="Search datasets and use cases"
            />
          </div>
        </div>

        {stats && (
        <div className="stats-strip">
          <div className="stat-strip-item">
            <span className="stat-strip-value is-primary">{animatedStats.projects}</span>
            <span className="stat-strip-label">Projects</span>
          </div>
          <span className="stat-strip-divider" aria-hidden="true"></span>
          <div className="stat-strip-item">
            <span className="stat-strip-value">{animatedStats.datasets}</span>
            <span className="stat-strip-label">Datasets</span>
          </div>
          <span className="stat-strip-divider" aria-hidden="true"></span>
          <div className="stat-strip-item">
            <span className="stat-strip-value">{animatedStats.usecases}</span>
            <span className="stat-strip-label">Pilots / Use cases</span>
          </div>
          <span className="stat-strip-divider" aria-hidden="true"></span>
          <div className="stat-strip-item">
            <span className="stat-strip-value">{animatedStats.countries}</span>
            <span className="stat-strip-label">Countries</span>
          </div>
          <Link to="/insights" className="stats-strip-link">
            Explore insights &amp; visualizations <i className="fas fa-arrow-right" aria-hidden="true"></i>
          </Link>
        </div>
        )}
      </div>
    </header>
  )
}

export default CatalogHeader

