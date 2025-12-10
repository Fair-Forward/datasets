import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import CatalogPage from './pages/CatalogPage'
import InsightsPage from './pages/InsightsPage'

// Derive a basename that works locally and on GitHub Pages
const getBaseName = () => {
  // Prefer document.baseURI so we honor the actual deployed path (e.g. /datasets/)
  const docBase = new URL(document.baseURI).pathname
  if (docBase && docBase !== '/') {
    return docBase.endsWith('/') ? docBase.slice(0, -1) : docBase
  }

  // Fallback to Vite's BASE_URL (may be "/" or "./")
  const envBase = import.meta.env.BASE_URL || '/'
  if (envBase === './') return '/'
  return envBase.endsWith('/') && envBase !== '/' ? envBase.slice(0, -1) : envBase
}

function App() {
  const basename = getBaseName()
  
  return (
    <Router basename={basename}>
      <Routes>
        <Route path="/" element={<CatalogPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/insights.html" element={<InsightsPage />} />
      </Routes>
    </Router>
  )
}

export default App

