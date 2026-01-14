import { useMemo, useState, useEffect, useRef, useCallback } from 'react'
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force'

// Parse organization strings like "Powered by: X\nCatalyzed by: Y\nFinanced by: Z"
const parseOrganizations = (orgString) => {
  if (!orgString || typeof orgString !== 'string') return null

  const result = {
    poweredBy: [],
    catalyzedBy: [],
    financedBy: []
  }

  const lines = orgString.split('\n')
  
  lines.forEach(line => {
    const lowerLine = line.toLowerCase()
    
    if (lowerLine.includes('powered by')) {
      const match = line.match(/powered by[:\s]+(.+)/i)
      if (match) {
        const orgs = match[1].split(/[,&]|(?:\s+and\s+)|(?:\s+in\s+(?:cooperation|collaboration|partnership)\s+with\s+)/i)
        orgs.forEach(org => {
          const cleaned = org.trim().replace(/^\s*[:\-]\s*/, '').trim()
          if (cleaned && cleaned.length > 1) {
            result.poweredBy.push(cleaned)
          }
        })
      }
    } else if (lowerLine.includes('catalyzed by')) {
      const match = line.match(/catalyzed by[:\s]+(.+)/i)
      if (match) {
        const orgs = match[1].split(/[,&]|(?:\s+and\s+)/i)
        orgs.forEach(org => {
          const cleaned = org.trim().replace(/^\s*[:\-]\s*/, '').trim()
          if (cleaned && cleaned.length > 1) {
            result.catalyzedBy.push(cleaned)
          }
        })
      }
    } else if (lowerLine.includes('financed by')) {
      const match = line.match(/financed by[:\s]+(.+)/i)
      if (match) {
        const orgs = match[1].split(/[,&]|(?:\s+and\s+)/i)
        orgs.forEach(org => {
          const cleaned = org.trim().replace(/^\s*[:\-]\s*/, '').trim()
          if (cleaned && cleaned.length > 1) {
            result.financedBy.push(cleaned)
          }
        })
      }
    }
  })

  return result
}

// Normalize organization names for grouping
const normalizeOrgName = (name) => {
  return name
    .toLowerCase()
    .replace(/\s*\([^)]*\)\s*/g, '')
    .replace(/https?:\/\/[^\s]+/g, '')
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

const OrganizationNetwork = ({ projects = [] }) => {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [selectedOrg, setSelectedOrg] = useState(null)
  const [hoveredOrg, setHoveredOrg] = useState(null)
  const [filter, setFilter] = useState('all')
  const [countryFilter, setCountryFilter] = useState('all')
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 })
  const [simulatedNodes, setSimulatedNodes] = useState([])
  const [simulatedLinks, setSimulatedLinks] = useState([])

  // Get all unique countries from projects
  const allCountries = useMemo(() => {
    const countries = new Set()
    projects.forEach(p => {
      (p.countries || []).forEach(c => countries.add(c))
    })
    return Array.from(countries).sort()
  }, [projects])

  // Filter projects by country
  const filteredProjects = useMemo(() => {
    if (countryFilter === 'all') return projects
    return projects.filter(p => (p.countries || []).includes(countryFilter))
  }, [projects, countryFilter])

  // Build organization data
  const { nodes, links, stats } = useMemo(() => {
    const orgMap = new Map()
    const projectOrgs = []

    filteredProjects.forEach(project => {
      const parsed = parseOrganizations(project.organizations)
      if (!parsed) return

      const projectOrgData = {
        projectId: project.id,
        projectTitle: project.title,
        orgs: { powered: [], catalyzed: [], financed: [] }
      }

      const processOrgs = (orgs, type, typeName) => {
        orgs.forEach(orgName => {
          const normalized = normalizeOrgName(orgName)
          if (!normalized || normalized.length < 2) return

          if (!orgMap.has(normalized)) {
            orgMap.set(normalized, {
              id: normalized,
              name: orgName,
              types: new Set(),
              projectCount: 0,
              projects: []
            })
          }

          const org = orgMap.get(normalized)
          org.types.add(type)
          org.projectCount++
          org.projects.push({ id: project.id, title: project.title })
          projectOrgData.orgs[typeName].push(normalized)
        })
      }

      processOrgs(parsed.poweredBy, 'powered', 'powered')
      processOrgs(parsed.catalyzedBy, 'catalyzed', 'catalyzed')
      processOrgs(parsed.financedBy, 'financed', 'financed')

      projectOrgs.push(projectOrgData)
    })

    // Convert to nodes array
    let nodeArray = Array.from(orgMap.values()).map(org => ({
      ...org,
      types: Array.from(org.types),
      primaryType: org.types.has('financed') ? 'financed' 
        : org.types.has('catalyzed') ? 'catalyzed' 
        : 'powered'
    }))

    // Apply type filter
    if (filter !== 'all') {
      nodeArray = nodeArray.filter(n => n.types.includes(filter))
    }

    // Sort by project count
    nodeArray.sort((a, b) => b.projectCount - a.projectCount)

    // Build links between orgs that share projects
    const linkMap = new Map()
    const nodeIds = new Set(nodeArray.map(n => n.id))
    
    projectOrgs.forEach(po => {
      const allOrgs = [...po.orgs.powered, ...po.orgs.catalyzed, ...po.orgs.financed]
        .filter(orgId => nodeIds.has(orgId))
      
      for (let i = 0; i < allOrgs.length; i++) {
        for (let j = i + 1; j < allOrgs.length; j++) {
          const key = [allOrgs[i], allOrgs[j]].sort().join('---')
          linkMap.set(key, (linkMap.get(key) || 0) + 1)
        }
      }
    })

    const linkArray = Array.from(linkMap.entries()).map(([key, count]) => {
      const [source, target] = key.split('---')
      return { source, target, count }
    })

    // Calculate stats
    const statsData = {
      totalOrgs: nodeArray.length,
      poweredBy: nodeArray.filter(n => n.types.includes('powered')).length,
      catalyzedBy: nodeArray.filter(n => n.types.includes('catalyzed')).length,
      financedBy: nodeArray.filter(n => n.types.includes('financed')).length,
      totalLinks: linkArray.length
    }

    return {
      nodes: nodeArray,
      links: linkArray,
      stats: statsData
    }
  }, [filteredProjects, filter])

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width } = containerRef.current.getBoundingClientRect()
        setDimensions({ width: Math.max(400, width - 48), height: 500 })
      }
    }
    
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Run force simulation
  useEffect(() => {
    if (nodes.length === 0) {
      setSimulatedNodes([])
      setSimulatedLinks([])
      return
    }

    const { width, height } = dimensions
    const maxProjectCount = Math.max(...nodes.map(n => n.projectCount), 1)
    
    // Create deep copies for simulation
    const simNodes = nodes.map(n => ({
      ...n,
      radius: 12 + (n.projectCount / maxProjectCount) * 28
    }))
    
    const simLinks = links.map(l => ({
      source: l.source,
      target: l.target,
      count: l.count
    }))

    const simulation = forceSimulation(simNodes)
      .force('link', forceLink(simLinks)
        .id(d => d.id)
        .distance(80)
        .strength(0.3))
      .force('charge', forceManyBody()
        .strength(-150))
      .force('center', forceCenter(width / 2, height / 2))
      .force('collision', forceCollide()
        .radius(d => d.radius + 8))

    simulation.on('tick', () => {
      // Constrain nodes within bounds
      simNodes.forEach(node => {
        node.x = Math.max(node.radius, Math.min(width - node.radius, node.x))
        node.y = Math.max(node.radius, Math.min(height - node.radius, node.y))
      })
    })

    simulation.on('end', () => {
      setSimulatedNodes([...simNodes])
      setSimulatedLinks([...simLinks])
    })

    // Run simulation faster
    for (let i = 0; i < 300; i++) simulation.tick()
    simulation.stop()
    
    setSimulatedNodes([...simNodes])
    setSimulatedLinks([...simLinks])

    return () => simulation.stop()
  }, [nodes, links, dimensions])

  // Get node color based on type
  const getNodeColor = (types) => {
    if (types.includes('financed')) return '#2563eb'
    if (types.includes('catalyzed')) return '#6366f1'
    return '#059669'
  }

  // Get connected nodes for highlighting
  const getConnectedNodes = useCallback((nodeId) => {
    const connected = new Set([nodeId])
    simulatedLinks.forEach(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source
      const targetId = typeof link.target === 'object' ? link.target.id : link.target
      if (sourceId === nodeId) connected.add(targetId)
      if (targetId === nodeId) connected.add(sourceId)
    })
    return connected
  }, [simulatedLinks])

  const handleNodeClick = (node) => {
    setSelectedOrg(selectedOrg?.id === node.id ? null : node)
  }

  const handleStatClick = (filterType) => {
    setFilter(filterType)
    setSelectedOrg(null)
  }

  const highlightedNodes = hoveredOrg ? getConnectedNodes(hoveredOrg.id) : null

  return (
    <div className="org-network-wrapper">
      {/* Controls Row */}
      <div className="org-network-controls">
        {/* Country Filter */}
        <div className="org-country-filter">
          <label htmlFor="country-select">
            <i className="fas fa-globe-africa"></i>
            Filter by Country
          </label>
          <select 
            id="country-select"
            value={countryFilter} 
            onChange={(e) => {
              setCountryFilter(e.target.value)
              setSelectedOrg(null)
            }}
          >
            <option value="all">All Countries ({projects.length} projects)</option>
            {allCountries.map(country => {
              const count = projects.filter(p => (p.countries || []).includes(country)).length
              return (
                <option key={country} value={country}>
                  {country} ({count} project{count !== 1 ? 's' : ''})
                </option>
              )
            })}
          </select>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="org-network-stats">
        <button 
          className={`org-stat org-stat-clickable ${filter === 'all' ? 'active' : ''}`}
          onClick={() => handleStatClick('all')}
        >
          <span className="org-stat-value">{stats.totalOrgs}</span>
          <span className="org-stat-label">Organizations</span>
        </button>
        <button 
          className={`org-stat org-stat-clickable ${filter === 'powered' ? 'active' : ''}`}
          onClick={() => handleStatClick('powered')}
        >
          <span className="org-stat-value org-stat-powered">{stats.poweredBy}</span>
          <span className="org-stat-label">Implementers</span>
        </button>
        <button 
          className={`org-stat org-stat-clickable ${filter === 'catalyzed' ? 'active' : ''}`}
          onClick={() => handleStatClick('catalyzed')}
        >
          <span className="org-stat-value org-stat-catalyzed">{stats.catalyzedBy}</span>
          <span className="org-stat-label">Catalysts</span>
        </button>
        <button 
          className={`org-stat org-stat-clickable ${filter === 'financed' ? 'active' : ''}`}
          onClick={() => handleStatClick('financed')}
        >
          <span className="org-stat-value org-stat-financed">{stats.financedBy}</span>
          <span className="org-stat-label">Financers</span>
        </button>
      </div>

      {/* Network Graph */}
      <div className="org-network-container" ref={containerRef}>
        {simulatedNodes.length > 0 ? (
          <svg 
            ref={svgRef}
            className="org-network-svg"
            width={dimensions.width} 
            height={dimensions.height}
            viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
          >
            <defs>
              {/* Gradient for links */}
              <linearGradient id="linkGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#94a3b8" stopOpacity="0.4" />
                <stop offset="50%" stopColor="#64748b" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#94a3b8" stopOpacity="0.4" />
              </linearGradient>
            </defs>

            {/* Links/Edges */}
            <g className="org-network-links">
              {simulatedLinks.map((link, i) => {
                const source = typeof link.source === 'object' ? link.source : 
                  simulatedNodes.find(n => n.id === link.source)
                const target = typeof link.target === 'object' ? link.target : 
                  simulatedNodes.find(n => n.id === link.target)
                
                if (!source || !target) return null

                const isHighlighted = highlightedNodes && 
                  (highlightedNodes.has(source.id) && highlightedNodes.has(target.id))
                const isSelected = selectedOrg && 
                  (source.id === selectedOrg.id || target.id === selectedOrg.id)
                
                const opacity = highlightedNodes 
                  ? (isHighlighted ? 0.8 : 0.08)
                  : selectedOrg
                    ? (isSelected ? 0.8 : 0.15)
                    : 0.35
                
                return (
                  <line
                    key={`link-${i}`}
                    className="org-network-link"
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke={isHighlighted || isSelected ? '#475569' : '#94a3b8'}
                    strokeWidth={Math.min(1 + link.count * 0.8, 4)}
                    strokeOpacity={opacity}
                    strokeLinecap="round"
                  />
                )
              })}
            </g>

            {/* Nodes */}
            <g className="org-network-nodes">
              {simulatedNodes.map((node) => {
                const isSelected = selectedOrg?.id === node.id
                const isHovered = hoveredOrg?.id === node.id
                const isConnected = highlightedNodes?.has(node.id)
                const dimmed = (highlightedNodes && !isConnected) || 
                  (selectedOrg && !isSelected && !getConnectedNodes(selectedOrg.id).has(node.id))
                
                return (
                  <g
                    key={node.id}
                    className={`org-network-node ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
                    transform={`translate(${node.x}, ${node.y})`}
                    onClick={() => handleNodeClick(node)}
                    onMouseEnter={() => setHoveredOrg(node)}
                    onMouseLeave={() => setHoveredOrg(null)}
                    style={{ cursor: 'pointer', opacity: dimmed ? 0.25 : 1 }}
                  >
                    {/* Node circle */}
                    <circle
                      r={node.radius}
                      fill={getNodeColor(node.types)}
                      stroke={isSelected || isHovered ? '#1e293b' : 'transparent'}
                      strokeWidth={isSelected ? 3 : 2}
                      className="org-node-circle"
                    />
                    
                    {/* Project count */}
                    <text
                      className="org-node-count"
                      textAnchor="middle"
                      dy="-0.1em"
                      fill="#fff"
                      fontSize={node.radius > 25 ? 14 : 11}
                      fontWeight="700"
                    >
                      {node.projectCount}
                    </text>
                    
                    {/* Organization name (for larger nodes) */}
                    {node.radius > 22 && (
                      <text
                        className="org-node-name"
                        textAnchor="middle"
                        dy="1em"
                        fill="#fff"
                        fontSize={8}
                        opacity={0.9}
                      >
                        {node.name.length > 12 ? node.name.slice(0, 10) + '..' : node.name}
                      </text>
                    )}

                    {/* Type indicators */}
                    <g transform={`translate(0, ${node.radius + 6})`}>
                      {node.types.map((type, i) => {
                        const offset = (i - (node.types.length - 1) / 2) * 10
                        return (
                          <circle
                            key={type}
                            cx={offset}
                            cy={0}
                            r={4}
                            fill={type === 'financed' ? '#2563eb' : type === 'catalyzed' ? '#6366f1' : '#059669'}
                            stroke="#fff"
                            strokeWidth={1.5}
                          />
                        )
                      })}
                    </g>
                  </g>
                )
              })}
            </g>
          </svg>
        ) : (
          <div className="org-network-empty">
            <i className="fas fa-project-diagram"></i>
            <p>No partnership data available for this selection</p>
          </div>
        )}

        {/* Selected Organization Detail Panel */}
        {selectedOrg && (
          <>
            <div 
              className="org-detail-backdrop"
              onClick={() => setSelectedOrg(null)}
            />
            <div className="org-detail-panel org-detail-panel-fixed">
              <button 
                className="org-detail-close"
                onClick={() => setSelectedOrg(null)}
                aria-label="Close"
              >
                <i className="fas fa-times"></i>
              </button>
              
              <div className="org-detail-header">
                <h3>{selectedOrg.name}</h3>
                <div className="org-detail-badges">
                  {selectedOrg.types.map(type => (
                    <span key={type} className={`org-detail-badge ${type}`}>
                      {type === 'powered' && 'Implementer'}
                      {type === 'catalyzed' && 'Catalyst'}
                      {type === 'financed' && 'Financer'}
                    </span>
                  ))}
                </div>
              </div>

              <div className="org-detail-connections">
                <h4>
                  <i className="fas fa-link"></i>
                  {getConnectedNodes(selectedOrg.id).size - 1} Partner Connection{getConnectedNodes(selectedOrg.id).size - 1 !== 1 ? 's' : ''}
                </h4>
              </div>

              <div className="org-detail-projects">
                <h4>
                  <i className="fas fa-folder-open"></i>
                  {selectedOrg.projectCount} Project{selectedOrg.projectCount !== 1 ? 's' : ''}
                </h4>
                <ul className="org-project-list">
                  {selectedOrg.projects.slice(0, 8).map(project => (
                    <li key={project.id}>
                      <a href={`#${project.id}`} className="org-project-link">
                        {project.title}
                      </a>
                    </li>
                  ))}
                  {selectedOrg.projects.length > 8 && (
                    <li className="org-project-more">
                      +{selectedOrg.projects.length - 8} more projects
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </>
        )}

        {/* Hover tooltip */}
        {hoveredOrg && !selectedOrg && (
          <div 
            className="org-hover-tooltip"
            style={{
              left: simulatedNodes.find(n => n.id === hoveredOrg.id)?.x || 0,
              top: (simulatedNodes.find(n => n.id === hoveredOrg.id)?.y || 0) - 
                   (simulatedNodes.find(n => n.id === hoveredOrg.id)?.radius || 0) - 45
            }}
          >
            <div className="org-tooltip-name">{hoveredOrg.name}</div>
            <div className="org-tooltip-meta">
              {hoveredOrg.projectCount} project{hoveredOrg.projectCount !== 1 ? 's' : ''} | 
              {getConnectedNodes(hoveredOrg.id).size - 1} connection{getConnectedNodes(hoveredOrg.id).size - 1 !== 1 ? 's' : ''}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="org-network-legend">
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: '#059669' }}></span>
          <span>Implementers</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: '#6366f1' }}></span>
          <span>Catalysts</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: '#2563eb' }}></span>
          <span>Financers</span>
        </div>
        <div className="org-legend-size">
          <span className="org-legend-dot-small"></span>
          <span className="org-legend-dot-large"></span>
          <span>Node size = project count</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-line"></span>
          <span>Lines = collaboration</span>
        </div>
      </div>

      {/* Network stats summary */}
      {stats.totalLinks > 0 && (
        <div className="org-network-summary">
          <span>{stats.totalLinks} collaboration{stats.totalLinks !== 1 ? 's' : ''} between organizations</span>
          {countryFilter !== 'all' && (
            <span className="org-network-filter-label">
              Showing partnerships in {countryFilter}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default OrganizationNetwork
