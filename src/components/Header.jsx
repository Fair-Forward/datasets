import { useState, useEffect, useRef, useCallback } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { withBasePath } from '../utils/basePath'

const Header = () => {
  const location = useLocation()
  const isInsights = location.pathname.includes('insights')
  const [infoType, setInfoType] = useState(null)
  const modalRef = useRef(null)
  const triggerRef = useRef(null)

  const closeInfo = useCallback(() => {
    setInfoType(null)
    triggerRef.current?.focus()
  }, [])

  // Escape key and focus trap for info modal
  useEffect(() => {
    if (!infoType) return
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        closeInfo()
        return
      }
      // Focus trap
      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll('button, a, [tabindex]:not([tabindex="-1"])')
        if (focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    // Move focus into modal
    const timer = setTimeout(() => {
      const firstFocusable = modalRef.current?.querySelector('button, a')
      firstFocusable?.focus()
    }, 50)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      clearTimeout(timer)
    }
  }, [infoType, closeInfo])

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
          <p className="info-card-note">
            All listed datasets and use-cases are shared as digital public goods from our partners. Please adhere to fair
            contributing: “This is a global digital public good under open-source licenses as named under ‘licenses’—please
            consider fair sharing and giving back to communities in an appropriate way.”
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
          <button type="button" className="header-info-button" onClick={() => { triggerRef.current = document.activeElement; setInfoType('about') }}>
            About this website
          </button>
          <button type="button" className="header-info-button" onClick={() => { triggerRef.current = document.activeElement; setInfoType('fair') }}>
            Fair sharing
          </button>
        </div>
        <nav className="top-nav-links" aria-label="Main navigation">
          <Link to="/" className={`nav-link ${!isInsights ? 'active' : ''}`} aria-current={!isInsights ? 'page' : undefined}>
            Projects
          </Link>
          <Link to="/insights" className={`nav-link ${isInsights ? 'active' : ''}`} aria-current={isInsights ? 'page' : undefined}>
            <i className="fas fa-chart-line" aria-hidden="true"></i> Insights
          </Link>
        </nav>
      </div>

      {infoType && (
        <>
          <div className="header-info-backdrop" onClick={closeInfo}></div>
          <div className="header-info-modal" role="dialog" aria-modal="true" ref={modalRef} aria-label={infoType === 'about' ? 'About this website' : 'Fair sharing'}>
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

