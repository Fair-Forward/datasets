import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import CatalogPage from './pages/CatalogPage'
import InsightsPage from './pages/InsightsPage'

// Derive a stable basename that works locally and on GitHub Pages.
// Uses the script URL to determine the deployment base path, which remains
// constant regardless of client-side navigation.
const getBaseName = () => {
  if (typeof document !== 'undefined') {
    const scriptEl = document.querySelector?.('script[type="module"][src]')
    const scriptSrc = scriptEl?.src
    if (scriptSrc && scriptSrc.includes('/assets/')) {
      const base = new URL(scriptSrc.split('/assets/')[0] + '/').pathname
      return base.endsWith('/') && base !== '/' ? base.slice(0, -1) : (base === '/' ? '' : base)
    }
  }

  // Fallback to Vite's BASE_URL (may be "/" or "./")
  const envBase = import.meta.env.BASE_URL || '/'
  if (envBase === './') return ''
  return envBase.endsWith('/') && envBase !== '/' ? envBase.slice(0, -1) : envBase
}

// Component to handle GitHub Pages SPA redirect
function GitHubPagesRedirect() {
  const navigate = useNavigate()
  const location = useLocation()
  
  useEffect(() => {
    // Check if we have a redirect path stored from 404.html
    const redirectPath = sessionStorage.getItem('gh-pages-redirect')
    if (redirectPath) {
      sessionStorage.removeItem('gh-pages-redirect')
      
      // Extract the route from the full path
      // e.g., /datasets/insights -> /insights
      const basename = getBaseName()
      let route = redirectPath
      
      if (basename && basename !== '/' && redirectPath.startsWith(basename)) {
        route = redirectPath.slice(basename.length) || '/'
      }
      
      // Navigate to the correct route
      if (route !== location.pathname) {
        navigate(route, { replace: true })
      }
    }
  }, [navigate, location.pathname])
  
  return null
}

function App() {
  const basename = getBaseName()
  
  return (
    <Router basename={basename}>
      <GitHubPagesRedirect />
      <Routes>
        <Route path="/" element={<CatalogPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/insights.html" element={<InsightsPage />} />
      </Routes>
    </Router>
  )
}

export default App
