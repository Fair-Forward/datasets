import { Link, useLocation } from 'react-router-dom'

const Header = () => {
  const location = useLocation()
  const isInsights = location.pathname.includes('insights')

  return (
    <div className="top-nav-container">
      <div className="top-nav-area">
        <div className="header-logos">
          <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank" rel="noopener noreferrer" title="Fair Forward Initiative">
            <img src="./img/ff_official.png" alt="Fair Forward Logo" className="header-logo" />
          </a>
          <a href="https://www.bmz-digital.global/en/" target="_blank" rel="noopener noreferrer" title="Digital Global">
            <img src="./img/digital_global_official.png" alt="Digital Global Logo" className="header-logo" />
          </a>
          <a href="https://www.bmz.de/en" target="_blank" rel="noopener noreferrer" title="Federal Ministry for Economic Cooperation and Development">
            <img src="./img/ministry_official.png" alt="BMZ Logo" className="header-logo" />
          </a>
        </div>
        <div className="top-nav-links">
          <Link to="/" className={`nav-link ${!isInsights ? 'active' : ''}`}>
            Catalog
          </Link>
          <Link to="/insights" className={`nav-link ${isInsights ? 'active' : ''}`}>
            <i className="fas fa-chart-line"></i> Insights
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Header

