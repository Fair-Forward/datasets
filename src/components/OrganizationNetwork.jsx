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

// Distinctive color palette
const COLORS = {
  powered: '#10b981',    // Emerald green - Implementers
  catalyzed: '#f59e0b',  // Amber/Orange - Catalysts  
  financed: '#8b5cf6'    // Purple - Financers
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
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })

  const MIN_ZOOM = 0.5
  const MAX_ZOOM = 3
  const ZOOM_STEP = 0.25

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

  // Build organization data (always from filteredProjects, filter applied separately for display)
  const { allNodes, allLinks, stats } = useMemo(() => {
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
    const nodeArray = Array.from(orgMap.values()).map(org => ({
      ...org,
      types: Array.from(org.types),
      primaryType: org.types.has('financed') ? 'financed' 
        : org.types.has('catalyzed') ? 'catalyzed' 
        : 'powered'
    }))

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

    // Calculate stats (always from full filtered set, not type-filtered)
    const statsData = {
      totalOrgs: nodeArray.length,
      poweredBy: nodeArray.filter(n => n.types.includes('powered')).length,
      catalyzedBy: nodeArray.filter(n => n.types.includes('catalyzed')).length,
      financedBy: nodeArray.filter(n => n.types.includes('financed')).length,
      totalLinks: linkArray.length
    }

    return {
      allNodes: nodeArray,
      allLinks: linkArray,
      stats: statsData
    }
  }, [filteredProjects])

  // Apply type filter for display
  const { nodes, links } = useMemo(() => {
    if (filter === 'all') {
      return { nodes: allNodes, links: allLinks }
    }
    
    const filteredNodes = allNodes.filter(n => n.types.includes(filter))
    const nodeIds = new Set(filteredNodes.map(n => n.id))
    const filteredLinks = allLinks.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target))
    
    return { nodes: filteredNodes, links: filteredLinks }
  }, [allNodes, allLinks, filter])

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
      radius: 14 + (n.projectCount / maxProjectCount) * 30
    }))
    
    const simLinks = links.map(l => ({
      source: l.source,
      target: l.target,
      count: l.count
    }))

    const simulation = forceSimulation(simNodes)
      .force('link', forceLink(simLinks)
        .id(d => d.id)
        .distance(100)
        .strength(0.4))
      .force('charge', forceManyBody()
        .strength(-200))
      .force('center', forceCenter(width / 2, height / 2))
      .force('collision', forceCollide()
        .radius(d => d.radius + 12))

    simulation.on('tick', () => {
      // Constrain nodes within bounds
      simNodes.forEach(node => {
        node.x = Math.max(node.radius + 20, Math.min(width - node.radius - 20, node.x))
        node.y = Math.max(node.radius + 20, Math.min(height - node.radius - 20, node.y))
      })
    })

    // Run simulation faster
    for (let i = 0; i < 300; i++) simulation.tick()
    simulation.stop()
    
    setSimulatedNodes([...simNodes])
    setSimulatedLinks([...simLinks])

    // Reset zoom and pan when data changes
    setZoom(1)
    setPan({ x: 0, y: 0 })

    return () => simulation.stop()
  }, [nodes, links, dimensions])

  // Get node color based on type
  const getNodeColor = (types) => {
    if (types.includes('financed')) return COLORS.financed
    if (types.includes('catalyzed')) return COLORS.catalyzed
    return COLORS.powered
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

  // Zoom handlers
  const handleZoomIn = () => {
    setZoom(z => Math.min(MAX_ZOOM, z + ZOOM_STEP))
  }

  const handleZoomOut = () => {
    setZoom(z => Math.max(MIN_ZOOM, z - ZOOM_STEP))
  }

  const handleZoomReset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const handleWheel = (e) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
    setZoom(z => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z + delta)))
  }

  // Pan handlers
  const handleMouseDown = (e) => {
    if (e.target.closest('.org-network-node')) return
    setIsPanning(true)
    setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
  }

  const handleMouseMove = (e) => {
    if (!isPanning) return
    setPan({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    })
  }

  const handleMouseUp = () => {
    setIsPanning(false)
  }

  const highlightedNodes = hoveredOrg ? getConnectedNodes(hoveredOrg.id) : null

  // Determine if names should show based on zoom level
  const showNames = zoom >= 1.5

  return (
    <div className="org-network-wrapper">
      {/* Stats Display (non-interactive) */}
      <div className="org-network-stats">
        <div className="org-stat">
          <span className="org-stat-value">{stats.totalOrgs}</span>
          <span className="org-stat-label">Organizations</span>
        </div>
        <div className="org-stat">
          <span className="org-stat-value org-stat-powered">{stats.poweredBy}</span>
          <span className="org-stat-label">Implementers</span>
        </div>
        <div className="org-stat">
          <span className="org-stat-value org-stat-catalyzed">{stats.catalyzedBy}</span>
          <span className="org-stat-label">Catalysts</span>
        </div>
        <div className="org-stat">
          <span className="org-stat-value org-stat-financed">{stats.financedBy}</span>
          <span className="org-stat-label">Financers</span>
        </div>
      </div>

      {/* Controls Row */}
      <div className="org-network-controls">
        {/* Country Filter */}
        <div className="org-filter-group">
          <label htmlFor="country-select">
            <i className="fas fa-globe-africa"></i>
            Country
          </label>
          <select 
            id="country-select"
            value={countryFilter} 
            onChange={(e) => {
              setCountryFilter(e.target.value)
              setSelectedOrg(null)
            }}
          >
            <option value="all">All Countries</option>
            {allCountries.map(country => {
              const count = projects.filter(p => (p.countries || []).includes(country)).length
              return (
                <option key={country} value={country}>
                  {country} ({count})
                </option>
              )
            })}
          </select>
        </div>

        {/* Type Filter */}
        <div className="org-filter-group">
          <label htmlFor="type-select">
            <i className="fas fa-filter"></i>
            Type
          </label>
          <select 
            id="type-select"
            value={filter} 
            onChange={(e) => {
              setFilter(e.target.value)
              setSelectedOrg(null)
            }}
          >
            <option value="all">All Types</option>
            <option value="powered">Implementers</option>
            <option value="catalyzed">Catalysts</option>
            <option value="financed">Financers</option>
          </select>
        </div>

        {/* Zoom Controls */}
        <div className="org-zoom-controls">
          <button 
            className="org-zoom-btn" 
            onClick={handleZoomOut}
            disabled={zoom <= MIN_ZOOM}
            title="Zoom out"
          >
            <i className="fas fa-minus"></i>
          </button>
          <span className="org-zoom-level">{Math.round(zoom * 100)}%</span>
          <button 
            className="org-zoom-btn" 
            onClick={handleZoomIn}
            disabled={zoom >= MAX_ZOOM}
            title="Zoom in"
          >
            <i className="fas fa-plus"></i>
          </button>
          <button 
            className="org-zoom-btn org-zoom-reset" 
            onClick={handleZoomReset}
            title="Reset view"
          >
            <i className="fas fa-compress-arrows-alt"></i>
          </button>
        </div>
      </div>

      {/* Network Graph */}
      <div 
        className="org-network-container" 
        ref={containerRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isPanning ? 'grabbing' : 'grab' }}
      >
        {simulatedNodes.length > 0 ? (
          <svg 
            ref={svgRef}
            className="org-network-svg"
            width={dimensions.width} 
            height={dimensions.height}
            viewBox={`0 0 ${dimensions.width} ${dimensions.height}`}
          >
            <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`} 
               style={{ transformOrigin: `${dimensions.width/2}px ${dimensions.height/2}px` }}>
              
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
                    ? (isHighlighted ? 0.7 : 0.06)
                    : selectedOrg
                      ? (isSelected ? 0.7 : 0.1)
                      : 0.25
                  
                  return (
                    <line
                      key={`link-${i}`}
                      className="org-network-link"
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      stroke={isHighlighted || isSelected ? '#64748b' : '#cbd5e1'}
                      strokeWidth={Math.min(1.5 + link.count * 0.8, 5)}
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
                      style={{ cursor: 'pointer', opacity: dimmed ? 0.2 : 1 }}
                    >
                      {/* Node circle */}
                      <circle
                        r={node.radius}
                        fill={getNodeColor(node.types)}
                        stroke={isSelected || isHovered ? '#1e293b' : 'rgba(255,255,255,0.5)'}
                        strokeWidth={isSelected ? 3 : 2}
                        className="org-node-circle"
                      />
                      
                      {/* Project count */}
                      <text
                        className="org-node-count"
                        textAnchor="middle"
                        dy={showNames ? "-0.3em" : "0.35em"}
                        fill="#fff"
                        fontSize={node.radius > 25 ? 14 : 12}
                        fontWeight="700"
                      >
                        {node.projectCount}
                      </text>
                      
                      {/* Organization name - visible when zoomed in */}
                      {showNames && (
                        <text
                          className="org-node-name"
                          textAnchor="middle"
                          dy="1em"
                          fill="#fff"
                          fontSize={9}
                          fontWeight="500"
                        >
                          {node.name.length > 16 ? node.name.slice(0, 14) + '..' : node.name}
                        </text>
                      )}

                      {/* Type indicator dot */}
                      <circle
                        cx={node.radius * 0.7}
                        cy={-node.radius * 0.7}
                        r={5}
                        fill={getNodeColor(node.types)}
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    </g>
                  )
                })}
              </g>
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
              left: (simulatedNodes.find(n => n.id === hoveredOrg.id)?.x || 0) * zoom + pan.x,
              top: ((simulatedNodes.find(n => n.id === hoveredOrg.id)?.y || 0) - 
                   (simulatedNodes.find(n => n.id === hoveredOrg.id)?.radius || 0) - 12) * zoom + pan.y - 40
            }}
          >
            <div className="org-tooltip-name">{hoveredOrg.name}</div>
            <div className="org-tooltip-meta">
              {hoveredOrg.projectCount} project{hoveredOrg.projectCount !== 1 ? 's' : ''} | 
              {getConnectedNodes(hoveredOrg.id).size - 1} connection{getConnectedNodes(hoveredOrg.id).size - 1 !== 1 ? 's' : ''}
            </div>
          </div>
        )}

        {/* Zoom hint */}
        {zoom === 1 && simulatedNodes.length > 0 && (
          <div className="org-zoom-hint">
            <i className="fas fa-search-plus"></i>
            Scroll to zoom, drag to pan
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="org-network-legend">
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: COLORS.powered }}></span>
          <span>Implementers</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: COLORS.catalyzed }}></span>
          <span>Catalysts</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: COLORS.financed }}></span>
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
          <span>{stats.totalLinks} collaboration{stats.totalLinks !== 1 ? 's' : ''} identified</span>
          {countryFilter !== 'all' && (
            <span className="org-network-filter-label">
              Showing: {countryFilter}
            </span>
          )}
          {filter !== 'all' && (
            <span className="org-network-filter-label">
              Type: {filter === 'powered' ? 'Implementers' : filter === 'catalyzed' ? 'Catalysts' : 'Financers'}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default OrganizationNetwork
