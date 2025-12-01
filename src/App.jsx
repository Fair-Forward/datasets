import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import CatalogPage from './pages/CatalogPage'
import InsightsPage from './pages/InsightsPage'

function App() {
  // Use base path from vite config (empty in dev, relative in production)
  const basename = import.meta.env.BASE_URL
  
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

