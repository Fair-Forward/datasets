import { useState, useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList
} from 'recharts'
import { withBasePath } from '../utils/basePath'

// Official SDG colors
const SDG_COLORS = {
  1: '#E5243B',   // No Poverty - Red
  2: '#DDA63A',   // Zero Hunger - Gold
  3: '#4C9F38',   // Good Health - Green
  4: '#C5192D',   // Quality Education - Dark Red
  5: '#FF3A21',   // Gender Equality - Orange Red
  6: '#26BDE2',   // Clean Water - Cyan
  7: '#FCC30B',   // Affordable Energy - Yellow
  8: '#A21942',   // Decent Work - Maroon
  9: '#FD6925',   // Industry Innovation - Orange
  10: '#DD1367',  // Reduced Inequalities - Magenta
  11: '#FD9D24',  // Sustainable Cities - Orange
  12: '#BF8B2E',  // Responsible Consumption - Brown Gold
  13: '#3F7E44',  // Climate Action - Forest Green
  14: '#0A97D9',  // Life Below Water - Blue
  15: '#56C02B',  // Life on Land - Bright Green
  16: '#00689D',  // Peace Justice - Dark Blue
  17: '#19486A'   // Partnerships - Navy
}

// SDG full names
const SDG_NAMES = {
  1: 'No Poverty',
  2: 'Zero Hunger',
  3: 'Good Health & Well-being',
  4: 'Quality Education',
  5: 'Gender Equality',
  6: 'Clean Water & Sanitation',
  7: 'Affordable & Clean Energy',
  8: 'Decent Work & Economic Growth',
  9: 'Industry, Innovation & Infrastructure',
  10: 'Reduced Inequalities',
  11: 'Sustainable Cities & Communities',
  12: 'Responsible Consumption & Production',
  13: 'Climate Action',
  14: 'Life Below Water',
  15: 'Life on Land',
  16: 'Peace, Justice & Strong Institutions',
  17: 'Partnerships for the Goals'
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  
  const data = payload[0].payload
  return (
    <div className="sdg-chart-tooltip">
      <div className="sdg-chart-tooltip-header" style={{ backgroundColor: data.color }}>
        <img 
          src={withBasePath(`img/sdg-${data.number}.png`)} 
          alt={`SDG ${data.number}`}
          className="sdg-chart-tooltip-icon"
        />
        <span>SDG {data.number}</span>
      </div>
      <div className="sdg-chart-tooltip-body">
        <div className="sdg-chart-tooltip-name">{data.fullName}</div>
        <div className="sdg-chart-tooltip-value">
          <span className="sdg-chart-tooltip-count">{data.count}</span>
          <span className="sdg-chart-tooltip-label">project{data.count !== 1 ? 's' : ''}</span>
        </div>
        <div className="sdg-chart-tooltip-percent">
          {data.percentage.toFixed(1)}% of total
        </div>
      </div>
    </div>
  )
}

const CustomLabel = ({ x, y, width, value, data }) => {
  if (width < 30) return null
  return (
    <text
      x={x + width - 8}
      y={y + 18}
      fill="#fff"
      fontSize={12}
      fontWeight={600}
      textAnchor="end"
    >
      {value}
    </text>
  )
}

const SDGChart = ({ sdgDistribution, onSDGClick }) => {
  const [hoveredSDG, setHoveredSDG] = useState(null)
  const [viewMode, setViewMode] = useState('bars') // 'bars' or 'grid'

  const chartData = useMemo(() => {
    if (!sdgDistribution) return []
    
    const total = Object.values(sdgDistribution).reduce((sum, count) => sum + count, 0)
    
    return Object.entries(sdgDistribution)
      .map(([sdg, count]) => {
        const number = parseInt(sdg.replace('SDG ', ''), 10)
        return {
          sdg,
          number,
          count,
          color: SDG_COLORS[number] || '#666',
          fullName: SDG_NAMES[number] || sdg,
          percentage: (count / total) * 100
        }
      })
      .sort((a, b) => b.count - a.count)
  }, [sdgDistribution])

  const totalProjects = useMemo(() => 
    chartData.reduce((sum, d) => sum + d.count, 0),
    [chartData]
  )

  const maxCount = useMemo(() => 
    Math.max(...chartData.map(d => d.count)),
    [chartData]
  )

  if (!chartData.length) {
    return <div className="sdg-chart-empty">No SDG data available</div>
  }

  return (
    <div className="sdg-chart-wrapper">
      {/* View mode toggle */}
      <div className="sdg-chart-controls">
        <div className="sdg-chart-summary">
          <span className="sdg-chart-summary-value">{chartData.length}</span>
          <span className="sdg-chart-summary-label">SDGs covered</span>
        </div>
        <div className="sdg-view-toggle">
          <button 
            className={`sdg-view-btn ${viewMode === 'bars' ? 'active' : ''}`}
            onClick={() => setViewMode('bars')}
            title="Bar chart view"
          >
            <i className="fas fa-chart-bar"></i>
          </button>
          <button 
            className={`sdg-view-btn ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
            title="Grid view"
          >
            <i className="fas fa-th-large"></i>
          </button>
        </div>
      </div>

      {viewMode === 'bars' ? (
        <div className="sdg-bars-container">
          {chartData.map((item, index) => (
            <div 
              key={item.sdg}
              className={`sdg-bar-row ${hoveredSDG === item.number ? 'hovered' : ''}`}
              onMouseEnter={() => setHoveredSDG(item.number)}
              onMouseLeave={() => setHoveredSDG(null)}
              onClick={() => onSDGClick?.(item)}
              style={{ '--delay': `${index * 50}ms` }}
            >
              <div className="sdg-bar-label">
                <img 
                  src={withBasePath(`img/sdg-${item.number}.png`)} 
                  alt={`SDG ${item.number}`}
                  className="sdg-bar-icon"
                  onError={(e) => { e.target.style.display = 'none' }}
                />
                <div className="sdg-bar-text">
                  <span className="sdg-bar-number">SDG {item.number}</span>
                  <span className="sdg-bar-name">{item.fullName}</span>
                </div>
              </div>
              <div className="sdg-bar-track">
                <div 
                  className="sdg-bar-fill"
                  style={{ 
                    width: `${(item.count / maxCount) * 100}%`,
                    backgroundColor: item.color,
                    '--bar-width': `${(item.count / maxCount) * 100}%`
                  }}
                >
                  <span className="sdg-bar-value">{item.count}</span>
                </div>
              </div>
              <div className="sdg-bar-percent">
                {item.percentage.toFixed(0)}%
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="sdg-grid-view">
          {chartData.map((item, index) => (
            <div 
              key={item.sdg}
              className="sdg-grid-card"
              style={{ 
                '--sdg-color': item.color,
                '--delay': `${index * 30}ms`
              }}
              onClick={() => onSDGClick?.(item)}
            >
              <div 
                className="sdg-grid-card-bg"
                style={{ backgroundColor: item.color }}
              />
              <img 
                src={withBasePath(`img/sdg-${item.number}.png`)} 
                alt={`SDG ${item.number}`}
                className="sdg-grid-icon"
                onError={(e) => { e.target.style.display = 'none' }}
              />
              <div className="sdg-grid-info">
                <span className="sdg-grid-count">{item.count}</span>
                <span className="sdg-grid-label">projects</span>
              </div>
              <div 
                className="sdg-grid-progress"
                style={{ 
                  width: `${item.percentage}%`,
                  backgroundColor: item.color
                }}
              />
            </div>
          ))}
        </div>
      )}

      {/* SDG Coverage Indicator */}
      <div className="sdg-coverage">
        <div className="sdg-coverage-label">Full SDG Coverage</div>
        <div className="sdg-coverage-track">
          {Array.from({ length: 17 }, (_, i) => i + 1).map(num => {
            const hasData = chartData.some(d => d.number === num)
            return (
              <div 
                key={num}
                className={`sdg-coverage-dot ${hasData ? 'active' : ''}`}
                style={{ backgroundColor: hasData ? SDG_COLORS[num] : undefined }}
                title={`SDG ${num}: ${SDG_NAMES[num]}`}
              />
            )
          })}
        </div>
        <div className="sdg-coverage-stat">
          {chartData.length} of 17 SDGs
        </div>
      </div>
    </div>
  )
}

export default SDGChart

