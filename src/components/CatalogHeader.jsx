import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

const CatalogHeader = ({ stats }) => {
  const [animatedStats, setAnimatedStats] = useState({
    projects: 0,
    datasets: 0,
    usecases: 0,
    countries: 0
  })

  // Animate counters on mount
  useEffect(() => {
    if (!stats) return

    const duration = 1500 // 1.5 seconds
    const steps = 60
    const interval = duration / steps

    let step = 0
    const timer = setInterval(() => {
      step++
      const progress = step / steps

      setAnimatedStats({
        projects: Math.floor(stats.total_projects * progress),
        datasets: Math.floor(stats.total_datasets * progress),
        usecases: Math.floor(stats.total_usecases * progress),
        countries: Math.floor(stats.total_countries * progress)
      })

      if (step >= steps) {
        clearInterval(timer)
        setAnimatedStats({
          projects: stats.total_projects,
          datasets: stats.total_datasets,
          usecases: stats.total_usecases,
          countries: stats.total_countries
        })
      }
    }, interval)

    return () => clearInterval(timer)
  }, [stats])

  if (!stats) return null

  return (
    <header>
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
                <span>Insights and Visualisations</span>
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

