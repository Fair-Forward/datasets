import { useMemo, useState } from 'react'
import { withBasePath } from '../utils/basePath'

// Define the maturity funnel stages in order of progression
const FUNNEL_STAGES = [
  { key: 'dataset', label: 'Datasets', icon: 'fa-database', color: '#3b82f6', patterns: ['dataset'] },
  { key: 'model', label: 'Models', icon: 'fa-brain', color: '#8b5cf6', patterns: ['model'] },
  { key: 'pilot', label: 'Pilots', icon: 'fa-flask', color: '#f59e0b', patterns: ['pilot'] },
  { key: 'usecase', label: 'Use Cases', icon: 'fa-lightbulb', color: '#06b6d4', patterns: ['use-case', 'use case', 'usecase'] },
  { key: 'business', label: 'Business Model', icon: 'fa-rocket', color: '#22c55e', patterns: ['business model', 'business-model', 'scaled'] }
]

// Parse maturity string and return which stages this project has reached
const parseMaturityStages = (maturityString) => {
  if (!maturityString || typeof maturityString !== 'string') return []
  
  const normalized = maturityString.toLowerCase().trim()
  const reachedStages = []
  
  // Check each stage - if any pattern matches, this project has reached that stage
  for (const stage of FUNNEL_STAGES) {
    for (const pattern of stage.patterns) {
      if (normalized.includes(pattern)) {
        reachedStages.push(stage.key)
        break // Found this stage, move to next
      }
    }
  }
  
  return reachedStages
}

const MaturityChart = ({ maturityDistribution, catalogProjects }) => {
  const [hoveredStage, setHoveredStage] = useState(null)

  // Process data - count projects that have reached EACH stage
  const sankeyData = useMemo(() => {
    // If we have raw catalog projects, use them for accurate counting
    // Otherwise fall back to the distribution (less accurate)
    let stageCounts = {}
    let totalProjects = 0
    
    FUNNEL_STAGES.forEach(stage => {
      stageCounts[stage.key] = 0
    })

    if (catalogProjects && Array.isArray(catalogProjects)) {
      // Count from raw project data - each project counts toward ALL stages it has reached
      totalProjects = catalogProjects.length
      
      catalogProjects.forEach(project => {
        const reachedStages = parseMaturityStages(project.maturity)
        reachedStages.forEach(stageKey => {
          stageCounts[stageKey] = (stageCounts[stageKey] || 0) + 1
        })
      })
    } else if (maturityDistribution) {
      // Fallback: parse the distribution keys and accumulate counts
      // This is less accurate but works if we only have aggregated data
      Object.entries(maturityDistribution).forEach(([maturityString, count]) => {
        const reachedStages = parseMaturityStages(maturityString)
        reachedStages.forEach(stageKey => {
          stageCounts[stageKey] = (stageCounts[stageKey] || 0) + count
        })
        totalProjects += count
      })
    }

    // Build stage data with counts
    const stages = FUNNEL_STAGES.map(stage => ({
      ...stage,
      count: stageCounts[stage.key] || 0,
      percentage: totalProjects > 0 ? (stageCounts[stage.key] / totalProjects) * 100 : 0
    }))

    const maxCount = Math.max(...stages.map(s => s.count), 1)

    return { stages, totalProjects, maxCount }
  }, [maturityDistribution, catalogProjects])

  if (!sankeyData || sankeyData.totalProjects === 0) {
    return <div className="maturity-chart-empty">No maturity data available</div>
  }

  const { stages, totalProjects, maxCount } = sankeyData

  // SVG dimensions
  const svgWidth = 800
  const svgHeight = 420
  const stageWidth = 120
  const stageGap = (svgWidth - (stages.length * stageWidth)) / (stages.length + 1)
  const maxFlowHeight = 260
  const topPadding = 70

  // Calculate positions and heights for each stage - height based on count
  const stagePositions = stages.map((stage, index) => {
    const x = stageGap + index * (stageWidth + stageGap)
    const heightRatio = stage.count / maxCount
    const height = Math.max(heightRatio * maxFlowHeight, 40)
    const y = topPadding + (maxFlowHeight - height) / 2
    
    return { x, y, width: stageWidth, height, stage }
  })

  // Create Sankey flow paths between stages
  const createFlowPath = (fromPos, toPos, fromStage, toStage) => {
    // Flow width is based on the smaller of the two connected stages
    const flowCount = Math.min(fromStage.count, toStage.count)
    if (flowCount <= 0) return null
    
    const flowHeightRatio = flowCount / maxCount
    const flowHeight = Math.max(flowHeightRatio * maxFlowHeight, 20)
    
    // Start from right side of 'from' box
    const x1 = fromPos.x + fromPos.width
    const y1Center = fromPos.y + fromPos.height / 2
    const y1Start = y1Center - flowHeight / 2
    const y1End = y1Center + flowHeight / 2
    
    // End at left side of 'to' box
    const x2 = toPos.x
    const y2Center = toPos.y + toPos.height / 2
    const y2Start = y2Center - flowHeight / 2
    const y2End = y2Center + flowHeight / 2
    
    // Control points for smooth curve
    const cpOffset = (x2 - x1) * 0.5
    
    return `
      M ${x1} ${y1Start}
      C ${x1 + cpOffset} ${y1Start}, ${x2 - cpOffset} ${y2Start}, ${x2} ${y2Start}
      L ${x2} ${y2End}
      C ${x2 - cpOffset} ${y2End}, ${x1 + cpOffset} ${y1End}, ${x1} ${y1End}
      Z
    `
  }

  return (
    <div className="sankey-chart-wrapper">
      {/* Header */}
      <div className="sankey-header">
        <div className="sankey-title">
          <span className="sankey-title-text">Project Maturity Pipeline</span>
          <span className="sankey-subtitle">How many projects have reached each stage</span>
        </div>
        <div className="sankey-total">
          <span className="sankey-total-value">{totalProjects}</span>
          <span className="sankey-total-label">Total Projects</span>
        </div>
      </div>

      {/* Progression indicator */}
      <div className="sankey-progression-indicator">
        <span>Maturity Progression</span>
        <i className="fas fa-long-arrow-alt-right"></i>
      </div>

      {/* Sankey Diagram */}
      <div className="sankey-container">
        <svg 
          viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
          className="sankey-svg"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Gradient definitions for flows */}
          <defs>
            {stagePositions.slice(0, -1).map((fromPos, index) => {
              const toPos = stagePositions[index + 1]
              return (
                <linearGradient key={`gradient-${index}`} id={`gradient-${index}`} x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor={fromPos.stage.color} />
                  <stop offset="100%" stopColor={toPos.stage.color} />
                </linearGradient>
              )
            })}
          </defs>

          {/* Flow paths between stages */}
          {stagePositions.slice(0, -1).map((fromPos, index) => {
            const toPos = stagePositions[index + 1]
            const path = createFlowPath(fromPos, toPos, fromPos.stage, toPos.stage)
            
            if (!path) return null
            
            const isHighlighted = hoveredStage === fromPos.stage.key || hoveredStage === toPos.stage.key
            
            return (
              <path
                key={`flow-${index}`}
                d={path}
                fill={`url(#gradient-${index})`}
                opacity={hoveredStage && !isHighlighted ? 0.2 : 0.5}
                className="sankey-flow"
              />
            )
          })}

          {/* Stage boxes */}
          {stagePositions.map((pos, index) => {
            const isHovered = hoveredStage === pos.stage.key
            const hasData = pos.stage.count > 0
            
            const handleStageClick = () => {
              if (hasData) {
                window.location.href = withBasePath(`/?view=${pos.stage.key}`)
              }
            }
            
            return (
              <g 
                key={pos.stage.key}
                className={`sankey-stage ${isHovered ? 'hovered' : ''} ${hasData ? 'has-data clickable' : 'empty'}`}
                onMouseEnter={() => setHoveredStage(pos.stage.key)}
                onMouseLeave={() => setHoveredStage(null)}
                onClick={handleStageClick}
                style={{ cursor: hasData ? 'pointer' : 'default' }}
              >
                {/* Stage rectangle */}
                <rect
                  x={pos.x}
                  y={pos.y}
                  width={pos.width}
                  height={pos.height}
                  rx={8}
                  fill={hasData ? pos.stage.color : '#e2e8f0'}
                  opacity={hoveredStage && !isHovered ? 0.4 : 1}
                  className="sankey-stage-rect"
                />
                
                {/* Stage count - inside the box */}
                <text
                  x={pos.x + pos.width / 2}
                  y={pos.y + pos.height / 2}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="sankey-stage-count"
                  fill="#fff"
                  fontSize={pos.height > 60 ? 28 : pos.height > 40 ? 22 : 16}
                  fontWeight="700"
                >
                  {pos.stage.count}
                </text>
              </g>
            )
          })}

          {/* Labels below stages */}
          {stagePositions.map((pos) => (
            <g key={`label-${pos.stage.key}`}>
              {/* Icon */}
              <foreignObject
                x={pos.x + pos.width / 2 - 16}
                y={topPadding + maxFlowHeight + 25}
                width={32}
                height={32}
              >
                <div 
                  className="sankey-label-icon"
                  style={{ color: pos.stage.color }}
                >
                  <i className={`fas ${pos.stage.icon}`}></i>
                </div>
              </foreignObject>
              
              {/* Label text */}
              <text
                x={pos.x + pos.width / 2}
                y={topPadding + maxFlowHeight + 70}
                textAnchor="middle"
                className="sankey-label-text"
                fill="var(--text)"
                fontSize={13}
                fontWeight="600"
              >
                {pos.stage.label}
              </text>
              
              {/* Percentage */}
              <text
                x={pos.x + pos.width / 2}
                y={topPadding + maxFlowHeight + 88}
                textAnchor="middle"
                className="sankey-label-percent"
                fill="var(--text-light)"
                fontSize={11}
              >
                {pos.stage.percentage.toFixed(0)}% of projects
              </text>
            </g>
          ))}

          {/* Drop-off indicators between stages */}
          {stagePositions.slice(0, -1).map((fromPos, index) => {
            const toPos = stagePositions[index + 1]
            const dropOff = fromPos.stage.count - toPos.stage.count
            const dropOffPercent = fromPos.stage.count > 0 
              ? ((dropOff / fromPos.stage.count) * 100).toFixed(0)
              : 0
            if (dropOff <= 0) return null
            
            const x = fromPos.x + fromPos.width + stageGap / 2
            const y = 30
            
            return (
              <g key={`dropoff-${index}`} className="sankey-dropoff">
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  className="sankey-dropoff-text"
                  fill="#ef4444"
                  fontSize={11}
                  fontWeight="600"
                >
                  −{dropOffPercent}%
                </text>
                <text
                  x={x}
                  y={y + 13}
                  textAnchor="middle"
                  className="sankey-dropoff-subtext"
                  fill="var(--text-light)"
                  fontSize={9}
                >
                  drop off
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Insight cards */}
      <div className="sankey-insights">
        <div className="sankey-insight-card">
          <div className="insight-card-icon" style={{ backgroundColor: '#dbeafe', color: '#3b82f6' }}>
            <i className="fas fa-database"></i>
          </div>
          <div className="insight-card-content">
            <span className="insight-card-value">{stages[0]?.count || 0}</span>
            <span className="insight-card-label">Have datasets</span>
          </div>
        </div>
        
        <div className="sankey-insight-card">
          <div className="insight-card-icon" style={{ backgroundColor: '#cffafe', color: '#06b6d4' }}>
            <i className="fas fa-lightbulb"></i>
          </div>
          <div className="insight-card-content">
            <span className="insight-card-value">{stages[3]?.count || 0}</span>
            <span className="insight-card-label">Reach use case stage</span>
          </div>
        </div>
        
        <div className="sankey-insight-card">
          <div className="insight-card-icon" style={{ backgroundColor: '#dcfce7', color: '#22c55e' }}>
            <i className="fas fa-rocket"></i>
          </div>
          <div className="insight-card-content">
            <span className="insight-card-value">{stages[4]?.count || 0}</span>
            <span className="insight-card-label">Have business model</span>
          </div>
        </div>
        
        <div className="sankey-insight-card highlight">
          <div className="insight-card-icon" style={{ backgroundColor: '#fef3c7', color: '#f59e0b' }}>
            <i className="fas fa-trophy"></i>
          </div>
          <div className="insight-card-content">
            <span className="insight-card-value">
              {stages[0]?.count > 0 
                ? ((stages[4]?.count / stages[0]?.count) * 100).toFixed(0) 
                : 0}%
            </span>
            <span className="insight-card-label">Full pipeline completion</span>
          </div>
        </div>
      </div>

      {/* Conversion funnel stats */}
      <div className="sankey-funnel-stats">
        <div className="funnel-stat-header">Stage-to-stage progression</div>
        <div className="funnel-stat-row">
          {stages.slice(1).map((stage, index) => {
            const prevStage = stages[index]
            const conversionRate = prevStage.count > 0 
              ? ((stage.count / prevStage.count) * 100).toFixed(0)
              : 0
            
            return (
              <div key={stage.key} className="funnel-stat">
                <div className="funnel-stat-arrow" style={{ color: stage.color }}>
                  <i className="fas fa-arrow-right"></i>
                </div>
                <div className="funnel-stat-content">
                  <span className="funnel-stat-value" style={{ color: stage.color }}>
                    {conversionRate}%
                  </span>
                  <span className="funnel-stat-label">
                    {prevStage.label} → {stage.label}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default MaturityChart
