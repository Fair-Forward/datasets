import { useState, useEffect, useMemo, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import CatalogHeader from '../components/CatalogHeader'
import FilterBar from '../components/FilterBar'
import ProjectCard from '../components/ProjectCard'
import DetailPanel from '../components/DetailPanel'
import Header from '../components/Header'
import Footer from '../components/Footer'
import { withBasePath } from '../utils/basePath'
import { rankScore } from '../utils/ranking'
import { matchesStatus, entryStatusValues, STATUS_OPTIONS } from '../utils/health'

const CatalogPage = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [catalogData, setCatalogData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedProject, setSelectedProject] = useState(null)

  // Handle project selection and URL updates
  const handleProjectSelect = useCallback((project) => {
    setSelectedProject(project)
    if (project) {
      const params = new URLSearchParams(searchParams)
      params.set('project', project.slug || project.id)
      setSearchParams(params, { replace: true })
    }
  }, [searchParams, setSearchParams])

  const handleProjectClose = useCallback(() => {
    setSelectedProject(null)
    const params = new URLSearchParams(searchParams)
    params.delete('project')
    setSearchParams(params, { replace: true })
  }, [searchParams, setSearchParams])

  // Initialize filters from URL params
  const getInitialFilters = useCallback(() => {
    return {
      search: searchParams.get('search') || '',
      view: searchParams.get('view') || 'all',
      sdg: searchParams.get('sdg') || '',
      dataType: searchParams.get('dataType') || '',
      // Support both 'country' and 'region' params
      country: searchParams.get('country') || searchParams.get('region') || '',
      maturity: searchParams.get('maturity') || '',
      status: searchParams.get('status') || ''
    }
  }, [searchParams])

  const [filters, setFilters] = useState(getInitialFilters)

  // Update filters when URL changes (e.g., from back/forward navigation)
  useEffect(() => {
    setFilters(getInitialFilters())
  }, [searchParams, getInitialFilters])

  // Update URL when filters change
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters)
    
    // Build new search params
    const params = new URLSearchParams()
    if (newFilters.search) params.set('search', newFilters.search)
    if (newFilters.view && newFilters.view !== 'all') params.set('view', newFilters.view)
    if (newFilters.sdg) params.set('sdg', newFilters.sdg)
    if (newFilters.dataType) params.set('dataType', newFilters.dataType)
    if (newFilters.country) params.set('region', newFilters.country)
    if (newFilters.maturity) params.set('maturity', newFilters.maturity)
    if (newFilters.status) params.set('status', newFilters.status)

    // Update URL without triggering navigation
    setSearchParams(params, { replace: true })
  }, [setSearchParams])

  const loadCatalog = useCallback(() => {
    setLoading(true)
    setError(null)
    // health.json is enriched separately (weekly) and merged here by id. A missing or
    // failed fetch must never break the catalog -- the signal is purely additive.
    const healthPromise = fetch(withBasePath('data/health.json'))
      .then(res => (res.ok ? res.json() : null))
      .catch(() => null)
    Promise.all([
      fetch(withBasePath('data/catalog.json')).then(res => {
        if (!res.ok) throw new Error('Failed to load catalog data')
        return res.json()
      }),
      healthPromise
    ])
      .then(([data, health]) => {
        if (health?.entries && Array.isArray(data.projects)) {
          data.projects = data.projects.map(p => ({ ...p, health: health.entries[p.id] || null }))
        }
        setCatalogData(data)
        setLoading(false)
        
        // Check if URL has a project param and open it
        const projectParam = searchParams.get('project')
        if (projectParam && data.projects) {
          let project = null

          // Try 1: extract ui_X prefix (handles new slugs and plain IDs)
          // Pattern matches the stable Project ID format from the Google Sheet
          const match = projectParam.match(/^(ui_\d+)/)
          if (match) {
            project = data.projects.find(p => p.id === match[1])
          }

          // Try 2: alias map (handles old title-based URLs)
          if (!project && data.aliases?.[projectParam]) {
            project = data.projects.find(p => p.id === data.aliases[projectParam])
          }

          if (project) {
            setSelectedProject(project)
            // Rewrite URL to canonical slug
            const canonicalSlug = project.slug || project.id
            if (projectParam !== canonicalSlug) {
              const params = new URLSearchParams(searchParams)
              params.set('project', canonicalSlug)
              setSearchParams(params, { replace: true })
            }
          }
        }
      })
      .catch(err => {
        console.error('Error loading catalog:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  // Load catalog data
  useEffect(() => { loadCatalog() }, [])

  // Status filter options, derived from the merged (weekly) health data. Only statuses actually
  // present are offered; if health.json failed to load there are none and the filter stays hidden.
  const availableStatuses = useMemo(() => {
    if (!catalogData?.projects) return []
    const present = new Set()
    catalogData.projects.forEach(p => entryStatusValues(p.health).forEach(v => present.add(v)))
    return STATUS_OPTIONS.filter(o => present.has(o.value))
  }, [catalogData])

  // Filter projects
  const filteredProjects = useMemo(() => {
    if (!catalogData?.projects) return []

    let projects = catalogData.projects

    // Search filter — searches across all meaningful text fields
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      projects = projects.filter(p => {
        const textFields = [
          p.title,
          p.description,
          p.organizations,
          p.contact,
          p.authors,
          p.data_characteristics,
          p.model_characteristics,
          p.how_to_use,
          p.license,
          p.access_note_markdown
        ]
        // Check plain text fields
        if (textFields.some(f => f && f.toLowerCase().includes(searchLower))) return true
        // Check array fields
        if (p.countries.some(c => c.toLowerCase().includes(searchLower))) return true
        if (p.sdgs.some(s => s.toLowerCase().includes(searchLower))) return true
        if (p.data_types.some(d => d.toLowerCase().includes(searchLower))) return true
        return false
      })
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

    // Maturity filter
    if (filters.maturity) {
      projects = projects.filter(p =>
        p.maturity_tags && p.maturity_tags.includes(filters.maturity)
      )
    }

    // Status filter (availability + activity). Only applied when the value is actually available,
    // so a stale/bookmarked ?status= with no health data loaded does not silently empty the catalog.
    if (filters.status && availableStatuses.some(o => o.value === filters.status)) {
      projects = projects.filter(p => matchesStatus(p.health, filters.status))
    }

    // View filter (datasets, use cases, lacuna, or maturity stages from Sankey)
    if (filters.view === 'datasets') {
      projects = projects.filter(p => p.has_dataset)
    } else if (filters.view === 'usecases') {
      projects = projects.filter(p => p.has_usecase)
    } else if (filters.view === 'info') {
      projects = projects.filter(p => p.has_access_note)
    } else if (filters.view === 'lacuna') {
      projects = projects.filter(p => p.is_lacuna)
    } else if (filters.view && filters.view !== 'all') {
      // Filter by maturity stage (from Sankey chart clicks)
      projects = projects.filter(p => 
        p.maturity_tags && p.maturity_tags.includes(filters.view)
      )
    }

    // Sort by combined rank: documentation depth, boosted by recent activity and link availability.
    // Copy first so we never sort catalogData.projects (state) in place.
    return [...projects].sort((a, b) => rankScore(b) - rankScore(a))
  }, [catalogData, filters, availableStatuses])

  // Calculate dynamic stats based on filtered results
  const dynamicStats = useMemo(() => {
    if (!catalogData?.stats) return null
    
    // Count datasets and usecases from filtered projects
    let datasetCount = 0
    let usecaseCount = 0
    let accessNoteCount = 0
    filteredProjects.forEach(p => {
      if (p.dataset_links) datasetCount += p.dataset_links.length
      if (p.usecase_links) usecaseCount += p.usecase_links.length
      if (p.has_access_note) accessNoteCount += 1
    })
    
    return {
      total_projects: filteredProjects.length,
      total_datasets: datasetCount,
      total_usecases: usecaseCount,
      total_access_note_projects: accessNoteCount,
      total_countries: new Set(filteredProjects.flatMap(p => p.countries || [])).size
    }
  }, [filteredProjects, catalogData])

  // Handle escape key to close panel
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && selectedProject) {
        handleProjectClose()
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [selectedProject, handleProjectClose])

  if (loading) {
    return (
      <div>
        <Header />
        <main>
          <div className="container">
            <div className="catalog-loading">
              <div className="insights-loading-spinner"></div>
              <p>Loading catalog...</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (error || !catalogData) {
    return (
      <div>
        <Header />
        <main>
          <div className="container">
            <div className="catalog-error">
              <i className="fas fa-exclamation-triangle"></i>
              <p>We could not load the catalog right now.</p>
              <button className="retry-btn" onClick={loadCatalog}>
                <i className="fas fa-rotate-right"></i> Try again
              </button>
              <p className="catalog-error-detail">
                If the problem persists, please{' '}
                <a href="https://github.com/Fair-Forward/datasets/issues" target="_blank" rel="noopener noreferrer">
                  report it on GitHub
                </a>.
              </p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div>
      <CatalogHeader
        stats={dynamicStats}
        search={filters.search}
        onSearchChange={(value) => handleFilterChange({ ...filters, search: value })}
      />

      <main id="main-content">
      <FilterBar 
        filters={filters} 
        onFilterChange={handleFilterChange}
        availableFilters={{
          ...catalogData.filters,
          statuses: availableStatuses,
          views: [
            { value: 'all', label: 'All items' },
            { value: 'datasets', label: 'Datasets' },
            { value: 'usecases', label: 'Use cases' },
            { value: 'info', label: 'Info (no public link)' },
            { value: 'lacuna', label: 'Lacuna Fund' }
          ]
        }}
      />
      
      <div className="container">
        <h2 className="sr-only">Project catalog</h2>
        <div className="results-bar" aria-live="polite">
          <div className="results-count">
            {filteredProjects.length} of {catalogData.stats.total_projects} results &middot; sorted by documentation depth
          </div>
          <div className="completeness-legend">
            <span className="completeness-legend-dots">
              {[1,2,3,4,5].map(i => <span key={i} className={`completeness-dot${i <= 4 ? ' filled' : ''}`} />)}
            </span>
            <span>= documentation depth</span>
          </div>
        </div>
        <div className="grid" id="dataGrid">
          {filteredProjects.map((project, idx) => (
            <ProjectCard
              key={project.id || idx}
              project={project}
              onClick={handleProjectSelect}
              onFilterSDG={(sdg) => handleFilterChange({ ...filters, sdg })}
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

      </main>

      {selectedProject && (
        <DetailPanel
          project={selectedProject}
          onClose={handleProjectClose}
        />
      )}

      <Footer />
    </div>
  )
}

export default CatalogPage
