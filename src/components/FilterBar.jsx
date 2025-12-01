import { useState } from 'react'

const FilterBar = ({ filters, onFilterChange, availableFilters }) => {
  const { sdgs = [], data_types = [], countries = [] } = availableFilters || {}
  const [searchTerm, setSearchTerm] = useState('')

  const handleSearchChange = (e) => {
    const value = e.target.value
    setSearchTerm(value)
    onFilterChange({ ...filters, search: value })
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
    setSearchTerm('')
    onFilterChange({ search: '', sdg: '', dataType: '', country: '' })
  }

  const hasActiveFilters = filters.search || filters.sdg || filters.dataType || filters.country

  return (
    <div className="filters">
      <div className="filter-row">
        <div className="search-container">
          <i className="fas fa-search search-icon"></i>
          <input 
            type="text" 
            className="search-input" 
            placeholder="Search projects..."
            value={searchTerm}
            onChange={handleSearchChange}
          />
        </div>
        
        <select 
          className="filter-select" 
          value={filters.sdg || ''} 
          onChange={handleSDGChange}
        >
          <option value="">All SDGs</option>
          {sdgs.map(sdg => (
            <option key={sdg} value={sdg}>{sdg}</option>
          ))}
        </select>
        
        <select 
          className="filter-select" 
          value={filters.dataType || ''} 
          onChange={handleDataTypeChange}
        >
          <option value="">All Data Types</option>
          {data_types.map(dt => (
            <option key={dt} value={dt}>{dt}</option>
          ))}
        </select>
        
        <select 
          className="filter-select" 
          value={filters.country || ''} 
          onChange={handleCountryChange}
        >
          <option value="">All Countries</option>
          {countries.map(country => (
            <option key={country} value={country}>{country}</option>
          ))}
        </select>
        
        {hasActiveFilters && (
          <button className="clear-filters-btn" onClick={clearFilters}>
            <i className="fas fa-times"></i> Clear
          </button>
        )}
      </div>
    </div>
  )
}

export default FilterBar

