import { useMemo, useState } from 'react'
import { withBasePath } from '../utils/basePath'

// SDG colors (official UN colors)
const SDG_COLORS = {
  1: '#E5243B', 2: '#DDA63A', 3: '#4C9F38', 4: '#C5192D',
  5: '#FF3A21', 6: '#26BDE2', 7: '#FCC30B', 8: '#A21942',
  9: '#FD6925', 10: '#DD1367', 11: '#FD9D24', 12: '#BF8B2E',
  13: '#3F7E44', 14: '#0A97D9', 15: '#56C02B', 16: '#00689D',
  17: '#19486A'
}

const SDGCountryHeatmap = ({ projects = [], onCellClick }) => {
  const [hoveredCell, setHoveredCell] = useState(null)
  const [sortBy, setSortBy] = useState('projects') // 'projects' | 'name' | 'sdgs'

  // Build the heatmap data
  const { matrix, countries, sdgs, maxCount } = useMemo(() => {
    // Get all unique countries and SDGs
    const countrySet = new Set()
    const sdgSet = new Set()
    const countryProjectCounts = {}
    const countrySDGCounts = {}

    projects.forEach(project => {
      (project.countries || []).forEach(country => {
        countrySet.add(country)
        countryProjectCounts[country] = (countryProjectCounts[country] || 0) + 1
      })
      ;(project.sdgs || []).forEach(sdg => {
        sdgSet.add(sdg)
      })
    })

    // Sort SDGs numerically
    const sdgList = Array.from(sdgSet).sort((a, b) => {
      const numA = parseInt(a.replace('SDG ', ''))
      const numB = parseInt(b.replace('SDG ', ''))
      return numA - numB
    })

    // Count SDGs per country
    projects.forEach(project => {
      (project.countries || []).forEach(country => {
        if (!countrySDGCounts[country]) countrySDGCounts[country] = new Set()
        ;(project.sdgs || []).forEach(sdg => countrySDGCounts[country].add(sdg))
      })
    })

    // Sort countries based on sortBy
    let countryList = Array.from(countrySet)
    if (sortBy === 'projects') {
      countryList.sort((a, b) => (countryProjectCounts[b] || 0) - (countryProjectCounts[a] || 0))
    } else if (sortBy === 'sdgs') {
      countryList.sort((a, b) => (countrySDGCounts[b]?.size || 0) - (countrySDGCounts[a]?.size || 0))
    } else {
      countryList.sort()
    }

    // Build the matrix
    const matrixData = {}
    let max = 0

    projects.forEach(project => {
      const projectCountries = project.countries || []
      const projectSDGs = project.sdgs || []

      projectCountries.forEach(country => {
        if (!matrixData[country]) matrixData[country] = {}
        projectSDGs.forEach(sdg => {
          matrixData[country][sdg] = (matrixData[country][sdg] || 0) + 1
          if (matrixData[country][sdg] > max) max = matrixData[country][sdg]
        })
      })
    })

    return {
      matrix: matrixData,
      countries: countryList,
      sdgs: sdgList,
      maxCount: max || 1
    }
  }, [projects, sortBy])

  // Get cell opacity based on count
  const getCellOpacity = (count) => {
    if (!count) return 0
    // Minimum opacity of 0.3 for visibility, max 1
    return 0.3 + (count / maxCount) * 0.7
  }

  // Get SDG number from label
  const getSDGNum = (sdg) => parseInt(sdg.replace('SDG ', ''))

  const handleCellClick = (country, sdg, count) => {
    if (count > 0 && onCellClick) {
      onCellClick({ country, sdg, count })
    }
  }

  if (countries.length === 0 || sdgs.length === 0) {
    return (
      <div className="heatmap-empty">
        <p>No data available for heatmap</p>
      </div>
    )
  }

  return (
    <div className="heatmap-wrapper">
      <div className="heatmap-controls">
        <label className="heatmap-sort-label">
          Sort countries by:
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="heatmap-sort-select"
          >
            <option value="projects">Most projects</option>
            <option value="sdgs">Most SDGs covered</option>
            <option value="name">Alphabetical</option>
          </select>
        </label>
      </div>

      <div className="heatmap-container">
        {/* SDG Header Row */}
        <div className="heatmap-header-row">
          <div className="heatmap-corner"></div>
          {sdgs.map(sdg => {
            const num = getSDGNum(sdg)
            return (
              <div 
                key={sdg} 
                className="heatmap-sdg-header"
                style={{ backgroundColor: SDG_COLORS[num] }}
                title={sdg}
              >
                <img 
                  src={withBasePath(`img/sdg-${num}.png`)} 
                  alt={sdg}
                  className="heatmap-sdg-icon"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
                <span className="heatmap-sdg-num">{num}</span>
              </div>
            )
          })}
        </div>

        {/* Country Rows */}
        <div className="heatmap-body">
          {countries.map(country => (
            <div key={country} className="heatmap-row">
              <div className="heatmap-country-label" title={country}>
                {country}
              </div>
              {sdgs.map(sdg => {
                const count = matrix[country]?.[sdg] || 0
                const num = getSDGNum(sdg)
                const isHovered = hoveredCell?.country === country && hoveredCell?.sdg === sdg
                
                return (
                  <div
                    key={`${country}-${sdg}`}
                    className={`heatmap-cell ${count > 0 ? 'has-data clickable' : ''} ${isHovered ? 'hovered' : ''}`}
                    style={{
                      backgroundColor: count > 0 
                        ? SDG_COLORS[num] 
                        : 'transparent',
                      opacity: count > 0 ? getCellOpacity(count) : 1
                    }}
                    onClick={() => handleCellClick(country, sdg, count)}
                    onMouseEnter={() => setHoveredCell({ country, sdg, count })}
                    onMouseLeave={() => setHoveredCell(null)}
                    title={count > 0 ? `${country}: ${count} project${count !== 1 ? 's' : ''} for ${sdg}` : ''}
                  >
                    {count > 0 && <span className="heatmap-cell-count">{count}</span>}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="heatmap-legend">
        <span className="heatmap-legend-label">Fewer projects</span>
        <div className="heatmap-legend-gradient">
          <div className="heatmap-legend-bar" style={{
            background: `linear-gradient(to right, rgba(100, 100, 100, 0.2), rgba(100, 100, 100, 0.5), rgba(100, 100, 100, 1))`
          }}></div>
        </div>
        <span className="heatmap-legend-label">More projects</span>
      </div>

      {/* Tooltip */}
      {hoveredCell && hoveredCell.count > 0 && (
        <div className="heatmap-tooltip-info">
          <strong>{hoveredCell.country}</strong> has <strong>{hoveredCell.count}</strong> project{hoveredCell.count !== 1 ? 's' : ''} addressing <strong>{hoveredCell.sdg}</strong>
          <span className="heatmap-tooltip-hint">Click to view projects</span>
        </div>
      )}
    </div>
  )
}

export default SDGCountryHeatmap

