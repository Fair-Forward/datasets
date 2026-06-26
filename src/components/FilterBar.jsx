const MATURITY_LABELS = {
  dataset: 'Datasets+',
  model: 'Models+',
  pilot: 'Pilots+',
  usecase: 'Use Cases+',
  business: 'Business Model'
}

const DEFAULT_VIEWS = [
  { value: 'all', label: 'All items' },
  { value: 'datasets', label: 'Datasets' },
  { value: 'usecases', label: 'Use cases' }
]

const FilterBar = ({ filters, onFilterChange, availableFilters }) => {
  const { sdgs = [], data_types = [], countries = [], maturity_stages = [], statuses = [] } = availableFilters || {}

  const handleSDGChange = (e) => {
    onFilterChange({ ...filters, sdg: e.target.value })
  }

  const handleDataTypeChange = (e) => {
    onFilterChange({ ...filters, dataType: e.target.value })
  }

  const handleCountryChange = (e) => {
    onFilterChange({ ...filters, country: e.target.value })
  }

  const handleMaturityChange = (e) => {
    onFilterChange({ ...filters, maturity: e.target.value })
  }

  const handleStatusChange = (e) => {
    onFilterChange({ ...filters, status: e.target.value })
  }

  const clearFilters = () => {
    onFilterChange({ search: '', view: 'all', sdg: '', dataType: '', country: '', maturity: '', status: '' })
  }

  const activeView = filters.view || 'all'
  const viewOptions = DEFAULT_VIEWS
  const hasActiveFilters = filters.search || filters.sdg || filters.dataType || filters.country || filters.maturity || filters.status || (filters.view && filters.view !== 'all')

  return (
    <div className="filters">
      <div className="filters-content">
        <div className="filter-segmented" role="group" aria-label="Filter by item type">
          {viewOptions.map((view) => (
            <button
              key={view.value}
              type="button"
              className={`segment${activeView === view.value ? ' active' : ''}`}
              onClick={() => onFilterChange({ ...filters, view: view.value })}
              aria-pressed={activeView === view.value}
            >
              {view.label}
            </button>
          ))}
        </div>

        <div className="filter-chips">
          <select
            className="filter-chip"
            value={filters.sdg || ''}
            onChange={handleSDGChange}
            aria-label="Filter by SDG"
          >
            <option value="">sdg: any</option>
            {sdgs.map(sdg => (
              <option key={sdg} value={sdg}>{sdg}</option>
            ))}
          </select>

          <select
            className="filter-chip"
            value={filters.country || ''}
            onChange={handleCountryChange}
            aria-label="Filter by country"
          >
            <option value="">country: any</option>
            {countries.map(country => (
              <option key={country} value={country}>{country}</option>
            ))}
          </select>

          <select
            className="filter-chip"
            value={filters.dataType || ''}
            onChange={handleDataTypeChange}
            aria-label="Filter by data type"
          >
            <option value="">type: any</option>
            {data_types.map(dt => (
              <option key={dt} value={dt}>{dt}</option>
            ))}
          </select>

          <select
            className="filter-chip"
            value={filters.maturity || ''}
            onChange={handleMaturityChange}
            aria-label="Filter by maturity stage"
          >
            <option value="">maturity: any</option>
            {maturity_stages.map(stage => (
              <option key={stage} value={stage}>
                {MATURITY_LABELS[stage] || stage}
              </option>
            ))}
          </select>

          {statuses.length > 0 && (
            <select
              className="filter-chip"
              value={filters.status || ''}
              onChange={handleStatusChange}
              aria-label="Filter by link status"
            >
              <option value="">status: any</option>
              {statuses.map(s => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          )}

          {hasActiveFilters && (
            <button className="clear-filters-btn" onClick={clearFilters}>
              <i className="fas fa-xmark"></i>
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default FilterBar
