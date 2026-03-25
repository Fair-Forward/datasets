const FilterBar = ({ filters, onFilterChange, availableFilters }) => {
  const { sdgs = [], data_types = [], countries = [], views = [] } = availableFilters || {}

  const handleSearchChange = (e) => {
    onFilterChange({ ...filters, search: e.target.value })
  }

  const handleSDGChange = (e) => {
    onFilterChange({ ...filters, sdg: e.target.value })
  }

  const handleDataTypeChange = (e) => {
    onFilterChange({ ...filters, dataType: e.target.value })
  }

  const handleCountryChange = (e) => {
    onFilterChange({ ...filters, country: e.target.value })
  }

  const clearFilters = () => {
    onFilterChange({ search: '', view: 'all', sdg: '', dataType: '', country: '' })
  }

  const hasActiveFilters = filters.search || filters.sdg || filters.dataType || filters.country || (filters.view && filters.view !== 'all')

  return (
    <div className="filters">
      <div className="filters-content">
        <div className="filter-group">
          <div className="search-box">
            <i className="fas fa-magnifying-glass"></i>
            <input
              type="text"
              placeholder="Search datasets and use-cases..."
              value={filters.search || ''}
              onChange={handleSearchChange}
              aria-label="Search datasets and use-cases"
            />
          </div>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-view">View:</label>
          <select
            id="filter-view"
            className="filter-select"
            value={filters.view || 'all'}
            onChange={(e) => onFilterChange({ ...filters, view: e.target.value })}
          >
            {(views.length ? views : [
              { value: 'all', label: 'All items' },
              { value: 'datasets', label: 'Datasets' },
              { value: 'usecases', label: 'Use cases' },
              { value: 'lacuna', label: 'Lacuna Fund' }
            ]).map((view) => (
              <option key={view.value} value={view.value}>{view.label}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-sdg">SDG:</label>
          <select
            id="filter-sdg"
            className="filter-select"
            value={filters.sdg || ''}
            onChange={handleSDGChange}
          >
            <option value="">All SDGs</option>
            {sdgs.map(sdg => (
              <option key={sdg} value={sdg}>{sdg}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-datatype">Data Type:</label>
          <select
            id="filter-datatype"
            className="filter-select"
            value={filters.dataType || ''}
            onChange={handleDataTypeChange}
          >
            <option value="">All Data Types</option>
            {data_types.map(dt => (
              <option key={dt} value={dt}>{dt}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label" htmlFor="filter-region">Region:</label>
          <select
            id="filter-region"
            className="filter-select"
            value={filters.country || ''}
            onChange={handleCountryChange}
          >
            <option value="">All Countries</option>
            {countries.map(country => (
              <option key={country} value={country}>{country}</option>
            ))}
          </select>
        </div>

        {hasActiveFilters && (
          <button className="clear-filters-btn" onClick={clearFilters}>
            <i className="fas fa-xmark"></i>
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}

export default FilterBar

