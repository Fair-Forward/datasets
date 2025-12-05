import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { withBasePath } from '../utils/basePath'

const Header = () => {
  const location = useLocation()
  const isInsights = location.pathname.includes('insights')
  const [infoType, setInfoType] = useState(null)

  const closeInfo = () => setInfoType(null)

  const renderInfoContent = () => {
    if (infoType === 'about') {
      return (
        <div className="info-card">
          <p className="info-card-eyebrow">About this website</p>
          <h4>Open data, open processes</h4>
          <p>
            This catalog is the public home for datasets, models, and pilots curated by Fair Forward and partners.
            Everything lives in versioned folders under <code>public/projects</code> so changes stay transparent and traceable.
          </p>
          <p>
            Data starts in the shared catalog spreadsheet, is transformed to JSON via our Python scripts, and is rendered here with a modern React frontend.
            All code and content remain open-source to keep collaboration lightweight and sustainable.
          </p>
          <div className="info-card-links">
            <a
              href="https://github.com/Fair-Forward/datasets#readme"
              target="_blank"
              rel="noopener noreferrer"
              className="info-card-link"
            >
              How this site is built
            </a>
            <a
              href="https://github.com/Fair-Forward/datasets/issues/new"
              target="_blank"
              rel="noopener noreferrer"
              className="info-card-link"
            >
              Share improvements
            </a>
          </div>
        </div>
      )
    }

    if (infoType === 'fair') {
      return (
        <div className="info-card">
          <p className="info-card-eyebrow">Fair sharing</p>
          <h4>Use responsibly &amp; credit communities</h4>
          <p>
            Every card lists the license and the organizations that made the data possible. When you reuse
            a dataset or model, cite the project, respect the license and let local partners know how your
            work gives back.
          </p>
          <div className="info-card-note">
            <span>Re-share improvements or context via GitHub or the listed contacts.</span>
          </div>
        </div>
      )
    }

    return null
  }

  return (
    <div className="top-nav-container">
      <div className="top-nav-area">
        <div className="top-nav-left">
          <div className="header-logos">
            <a href="https://www.bmz-digital.global/en/overview-of-initiatives/fair-forward/" target="_blank" rel="noopener noreferrer" title="Fair Forward Initiative">
              <img src={withBasePath('img/ff_official.png')} alt="Fair Forward Logo" className="header-logo" />
            </a>
            <a href="https://www.bmz-digital.global/en/" target="_blank" rel="noopener noreferrer" title="Digital Global">
              <img src={withBasePath('img/digital_global_official.png')} alt="Digital Global Logo" className="header-logo" />
            </a>
            <a href="https://www.giz.de/en/html/index.html" target="_blank" rel="noopener noreferrer" title="Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ)">
              <img src={withBasePath('img/giz_official.png')} alt="GIZ Logo" className="header-logo" />
            </a>
            <a href="https://www.bmz.de/en" target="_blank" rel="noopener noreferrer" title="Federal Ministry for Economic Cooperation and Development">
              <img src={withBasePath('img/ministry_official.png')} alt="BMZ Logo" className="header-logo" />
            </a>
          </div>
        </div>
        <div className="header-info-links">
          <button type="button" className="header-info-button" onClick={() => setInfoType('about')}>
            About this website
          </button>
          <button type="button" className="header-info-button" onClick={() => setInfoType('fair')}>
            Fair sharing
          </button>
        </div>
        <div className="top-nav-links">
          <Link to="/" className={`nav-link ${!isInsights ? 'active' : ''}`}>
            Projects
          </Link>
          <Link to="/insights" className={`nav-link ${isInsights ? 'active' : ''}`}>
            <i className="fas fa-chart-line"></i> Insights
          </Link>
        </div>
      </div>

      {infoType && (
        <>
          <div className="header-info-backdrop" onClick={closeInfo}></div>
          <div className="header-info-modal" role="dialog" aria-modal="true">
            <button className="header-info-close" onClick={closeInfo} aria-label="Close info panel">
              <i className="fas fa-times"></i>
            </button>
            {renderInfoContent()}
          </div>
        </>
      )}
    </div>
  )
}

export default Header

