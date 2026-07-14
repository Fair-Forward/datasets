import { useState } from 'react'

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

  // Type / Maturity / Status are secondary; keep them tucked away so the primary
  // decision point stays small. Open by default only when one is already applied
  // (e.g. arriving via a shared URL) so the active filter is never hidden.
  const advancedActiveCount = [filters.dataType, filters.maturity, filters.status].filter(Boolean).length
  const [showMore, setShowMore] = useState(() => advancedActiveCount > 0)

  const setFilter = (patch) => onFilterChange({ ...filters, ...patch })

  const clearFilters = () => {
    onFilterChange({ search: '', view: 'all', sdg: '', dataType: '', country: '', maturity: '', status: '' })
  }

  const activeView = filters.view || 'all'
  const statusLabel = (value) => statuses.find(s => s.value === value)?.label || value

  const hasActiveFilters = filters.search || filters.sdg || filters.dataType || filters.country ||
    filters.maturity || filters.status || (filters.view && filters.view !== 'all')

  // Applied filters, surfaced as removable chips so what's active is recognizable
  // rather than something the user has to re-open each dropdown to recall.
  const activeChips = []
  if (filters.sdg) activeChips.push({ key: 'sdg', label: /^sdg/i.test(filters.sdg) ? filters.sdg : `SDG: ${filters.sdg}`, clear: () => setFilter({ sdg: '' }) })
  if (filters.country) activeChips.push({ key: 'country', label: `Country: ${filters.country}`, clear: () => setFilter({ country: '' }) })
  if (filters.dataType) activeChips.push({ key: 'dataType', label: `Type: ${filters.dataType}`, clear: () => setFilter({ dataType: '' }) })
  if (filters.maturity) activeChips.push({ key: 'maturity', label: `Maturity: ${MATURITY_LABELS[filters.maturity] || filters.maturity}`, clear: () => setFilter({ maturity: '' }) })
  if (filters.status) activeChips.push({ key: 'status', label: `Status: ${statusLabel(filters.status)}`, clear: () => setFilter({ status: '' }) })

  return (
    <div className="filters">
      <div className="filters-content">
        <div className="filter-segmented" role="group" aria-label="Filter by item type">
          {DEFAULT_VIEWS.map((view) => (
            <button
              key={view.value}
              type="button"
              className={`segment${activeView === view.value ? ' active' : ''}`}
              onClick={() => setFilter({ view: view.value })}
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
            onChange={(e) => setFilter({ sdg: e.target.value })}
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
            onChange={(e) => setFilter({ country: e.target.value })}
            aria-label="Filter by country"
          >
            <option value="">country: any</option>
            {countries.map(country => (
              <option key={country} value={country}>{country}</option>
            ))}
          </select>

          <button
            type="button"
            className={`more-filters-btn${showMore ? ' open' : ''}`}
            onClick={() => setShowMore(v => !v)}
            aria-expanded={showMore}
            aria-controls="filters-drawer"
          >
            <i className="fas fa-sliders" aria-hidden="true"></i>
            More filters{advancedActiveCount > 0 ? ` (${advancedActiveCount})` : ''}
          </button>

          {hasActiveFilters && (
            <button className="clear-filters-btn" onClick={clearFilters}>
              <i className="fas fa-xmark" aria-hidden="true"></i>
              Clear
            </button>
          )}
        </div>
      </div>

      {showMore && (
        <div className="filters-drawer" id="filters-drawer">
          <div className="filters-drawer-inner">
            <select
              className="filter-chip"
              value={filters.dataType || ''}
              onChange={(e) => setFilter({ dataType: e.target.value })}
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
              onChange={(e) => setFilter({ maturity: e.target.value })}
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
                onChange={(e) => setFilter({ status: e.target.value })}
                aria-label="Filter by link status"
              >
                <option value="">status: any</option>
                {statuses.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      )}

      {activeChips.length > 0 && (
        <div className="filters-active">
          <div className="filters-active-inner">
            {activeChips.map(chip => (
              <button
                key={chip.key}
                type="button"
                className="filter-active-chip"
                onClick={chip.clear}
                aria-label={`Remove filter ${chip.label}`}
              >
                {chip.label}
                <i className="fas fa-xmark" aria-hidden="true"></i>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default FilterBar
