import { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import CatalogPage from './pages/CatalogPage'
import InsightsPage from './pages/InsightsPage'
import { withBasePath } from './utils/basePath'

// Get the basename for React Router by using the same base path utility.
// Remove trailing slash for Router basename (it adds one automatically).
const getBaseName = () => {
  const base = withBasePath('')
  // withBasePath('') returns something like '/datasets/' - remove trailing slash
  return base.endsWith('/') && base.length > 1 ? base.slice(0, -1) : (base === '/' ? '' : base)
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
