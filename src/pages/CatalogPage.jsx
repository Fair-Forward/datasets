import { useState, useEffect, useMemo } from 'react'
import CatalogHeader from '../components/CatalogHeader'
import FilterBar from '../components/FilterBar'
import ProjectCard from '../components/ProjectCard'
import DetailPanel from '../components/DetailPanel'
import Header from '../components/Header'
import { withBasePath } from '../utils/basePath'

const CatalogPage = () => {
  const [catalogData, setCatalogData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({
    search: '',
    view: 'all',
    sdg: '',
    dataType: '',
    country: ''
  })
  const [selectedProject, setSelectedProject] = useState(null)

  // Load catalog data
  useEffect(() => {
    fetch(withBasePath('data/catalog.json'))
      .then(res => {
        if (!res.ok) throw new Error('Failed to load catalog data')
        return res.json()
      })
      .then(data => {
        setCatalogData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading catalog:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  // Filter projects
  const filteredProjects = useMemo(() => {
    if (!catalogData?.projects) return []

    let projects = catalogData.projects

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      projects = projects.filter(p =>
        p.title.toLowerCase().includes(searchLower) ||
        p.description.toLowerCase().includes(searchLower) ||
        p.countries.some(c => c.toLowerCase().includes(searchLower)) ||
        p.sdgs.some(s => s.toLowerCase().includes(searchLower))
      )
    }

    // SDG filter
    if (filters.sdg) {
      projects = projects.filter(p => p.sdgs.includes(filters.sdg))
    }

    // Data type filter
    if (filters.dataType) {
      projects = projects.filter(p => p.data_types.includes(filters.dataType))
    }

    // Country filter
    if (filters.country) {
      projects = projects.filter(p => p.countries.includes(filters.country))
    }

    // View filter (datasets, use cases, lacuna)
    if (filters.view === 'datasets') {
      projects = projects.filter(p => p.has_dataset)
    } else if (filters.view === 'usecases') {
      projects = projects.filter(p => p.has_usecase)
    } else if (filters.view === 'lacuna') {
      projects = projects.filter(p => p.is_lacuna)
    }

    return projects
  }, [catalogData, filters])

  // Calculate dynamic stats based on filtered results
  const dynamicStats = useMemo(() => {
    if (!catalogData?.stats) return null
    
    // Count datasets and usecases from filtered projects
    let datasetCount = 0
    let usecaseCount = 0
    filteredProjects.forEach(p => {
      if (p.dataset_links) datasetCount += p.dataset_links.length
      if (p.usecase_links) usecaseCount += p.usecase_links.length
    })
    
    return {
      total_projects: filteredProjects.length,
      total_datasets: datasetCount,
      total_usecases: usecaseCount,
      total_countries: new Set(filteredProjects.flatMap(p => p.countries || [])).size
    }
  }, [filteredProjects, catalogData])

  // Handle escape key to close panel
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && selectedProject) {
        setSelectedProject(null)
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [selectedProject])

  if (loading) {
    return (
      <div>
        <Header />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '4rem' }}>
            <p>Loading catalog...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !catalogData) {
    return (
      <div>
        <Header />
        <div className="container">
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-light)' }}>
            <p>Unable to load catalog data. Please run the build script.</p>
            <p style={{ fontSize: '0.9rem', marginTop: '1rem' }}>
              Error: {error || 'No data available'}
            </p>
            <code style={{ display: 'block', marginTop: '1rem', padding: '1rem', background: '#f5f5f5' }}>
              python scripts/generate_catalog_data.py
            </code>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <CatalogHeader stats={dynamicStats} />
      
      <FilterBar 
        filters={filters} 
        onFilterChange={setFilters}
        availableFilters={{
          ...catalogData.filters,
          views: [
            { value: 'all', label: 'All items' },
            { value: 'datasets', label: 'Datasets' },
            { value: 'usecases', label: 'Use cases' },
            { value: 'lacuna', label: 'Lacuna Fund' }
          ]
        }}
      />
      
      <div className="container">
        <div className="grid" id="dataGrid">
          {filteredProjects.map((project, idx) => (
            <ProjectCard 
              key={project.id || idx} 
              project={project}
              onClick={setSelectedProject}
            />
          ))}
        </div>
        
        {filteredProjects.length === 0 && (
          <div className="empty-state visible">
            <h3>No matching items found</h3>
            <p>Try adjusting your filters or search term to find what you're looking for.</p>
          </div>
        )}
      </div>

      {selectedProject && (
        <DetailPanel 
          project={selectedProject} 
          onClose={() => setSelectedProject(null)}
        />
      )}

      <footer>
        <div className="footer-content">
          <p>&copy; {new Date().getFullYear()} Fair Forward - Artificial Intelligence for All | A project by GIZ</p>
          <p style={{ marginTop: '1rem', fontSize: '0.875rem' }}>
            <a href="https://github.com/Fair-Forward/datasets" target="_blank" rel="noopener noreferrer" 
               style={{ color: 'var(--primary)', textDecoration: 'none' }}>
              Contribute to the Source Code on GitHub <i className="fab fa-github"></i>
            </a>
          </p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
            For technical questions/feedback{' '}
            <a href="https://github.com/Fair-Forward/datasets/issues" target="_blank" rel="noopener noreferrer"
               style={{ color: 'var(--primary)' }}>
              open an issue on Github
            </a>
            {' '}or contact{' '}
            <a href="mailto:jonas.nothnagel@gmail.com" style={{ color: 'var(--primary)' }}>
              Jonas Nothnagel
            </a>.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default CatalogPage
