import { useMemo, useState, useEffect, useRef } from 'react'

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
        // Split by common separators and clean up
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
    .replace(/\s*\([^)]*\)\s*/g, '') // Remove parenthetical content
    .replace(/https?:\/\/[^\s]+/g, '') // Remove URLs
    .replace(/[^\w\s]/g, '') // Remove special chars
    .replace(/\s+/g, ' ')
    .trim()
}

const OrganizationNetwork = ({ projects = [] }) => {
  const containerRef = useRef(null)
  const [selectedOrg, setSelectedOrg] = useState(null)
  const [selectedPosition, setSelectedPosition] = useState({ x: 0, y: 0 })
  const [hoveredOrg, setHoveredOrg] = useState(null)
  const [filter, setFilter] = useState('all') // 'all' | 'powered' | 'catalyzed' | 'financed'
  const [showAll, setShowAll] = useState(false)
  const INITIAL_DISPLAY_COUNT = 30

  // Build organization data
  const { nodes, links, orgToProjects, stats } = useMemo(() => {
    const orgMap = new Map() // normalized name -> { name, type, count, projects }
    const projectOrgs = [] // array of { projectId, orgs: { powered, catalyzed, financed } }

    projects.forEach(project => {
      const parsed = parseOrganizations(project.organizations)
      if (!parsed) return

      const projectOrgData = {
        projectId: project.id,
        projectTitle: project.title,
        orgs: { powered: [], catalyzed: [], financed: [] }
      }

      // Process each type
      const processOrgs = (orgs, type, typeName) => {
        orgs.forEach(orgName => {
          const normalized = normalizeOrgName(orgName)
          if (!normalized || normalized.length < 2) return

          if (!orgMap.has(normalized)) {
            orgMap.set(normalized, {
              id: normalized,
              name: orgName, // Keep original for display
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
    projectOrgs.forEach(po => {
      const allOrgs = [...po.orgs.powered, ...po.orgs.catalyzed, ...po.orgs.financed]
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

    // Create lookup for org -> projects
    const orgToProjectsMap = new Map()
    nodeArray.forEach(node => {
      orgToProjectsMap.set(node.id, node.projects)
    })

    // Calculate stats
    const statsData = {
      totalOrgs: nodeArray.length,
      poweredBy: nodeArray.filter(n => n.types.includes('powered')).length,
      catalyzedBy: nodeArray.filter(n => n.types.includes('catalyzed')).length,
      financedBy: nodeArray.filter(n => n.types.includes('financed')).length,
      avgProjectsPerOrg: nodeArray.length > 0 
        ? (nodeArray.reduce((sum, n) => sum + n.projectCount, 0) / nodeArray.length).toFixed(1)
        : 0
    }

    return {
      nodes: nodeArray,
      links: linkArray,
      orgToProjects: orgToProjectsMap,
      stats: statsData
    }
  }, [projects])

  // Filter nodes based on selected filter
  const filteredNodes = useMemo(() => {
    if (filter === 'all') return nodes
    return nodes.filter(n => n.types.includes(filter))
  }, [nodes, filter])

  // Get node color based on type - muted, professional palette
  const getNodeColor = (types) => {
    if (types.includes('financed')) return '#2563eb' // Deep blue for financers
    if (types.includes('catalyzed')) return '#6366f1' // Indigo for catalysts
    return '#059669' // Teal/emerald for implementers
  }

  // Handle bubble click with position tracking
  const handleBubbleClick = (node, event) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const containerRect = containerRef.current?.getBoundingClientRect() || { left: 0, top: 0 }
    
    setSelectedPosition({
      x: rect.left - containerRect.left + rect.width / 2,
      y: rect.top - containerRect.top + rect.height + 10
    })
    setSelectedOrg(selectedOrg?.id === node.id ? null : node)
  }

  // Get node size based on project count
  const getNodeSize = (count, max) => {
    const minSize = 40
    const maxSize = 100
    return minSize + (count / max) * (maxSize - minSize)
  }

  const maxProjectCount = Math.max(...nodes.map(n => n.projectCount), 1)

  // Handle stat click to filter
  const handleStatClick = (filterType) => {
    setFilter(filterType)
    setShowAll(false) // Reset expansion when changing filter
  }

  return (
    <div className="org-network-wrapper">
      {/* Stats Bar - Clickable */}
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

      {/* Network Visualization - Bubble/Cluster Layout */}
      <div className="org-network-container" ref={containerRef}>
        <div className="org-bubble-grid">
          {(showAll ? filteredNodes : filteredNodes.slice(0, INITIAL_DISPLAY_COUNT)).map((node, index) => {
            const size = getNodeSize(node.projectCount, maxProjectCount)
            const isSelected = selectedOrg?.id === node.id
            const isHovered = hoveredOrg?.id === node.id
            
            return (
              <div
                key={node.id}
                className={`org-bubble ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
                style={{
                  '--bubble-size': `${size}px`,
                  '--bubble-color': getNodeColor(node.types),
                  animationDelay: `${Math.min(index, 30) * 0.03}s`
                }}
                onClick={(e) => handleBubbleClick(node, e)}
                onMouseEnter={() => setHoveredOrg(node)}
                onMouseLeave={() => setHoveredOrg(null)}
              >
                <div className="org-bubble-inner">
                  <span className="org-bubble-count">{node.projectCount}</span>
                  <span className="org-bubble-name">{node.name}</span>
                </div>
                <div className="org-bubble-types">
                  {node.types.includes('powered') && <span className="org-type-badge powered" title="Implementer"></span>}
                  {node.types.includes('catalyzed') && <span className="org-type-badge catalyzed" title="Catalyst"></span>}
                  {node.types.includes('financed') && <span className="org-type-badge financed" title="Financer"></span>}
                </div>
              </div>
            )
          })}
        </div>

        {filteredNodes.length > INITIAL_DISPLAY_COUNT && (
          <div className="org-expand-controls">
            {!showAll ? (
              <button className="org-expand-btn" onClick={() => setShowAll(true)}>
                <i className="fas fa-chevron-down"></i>
                Show all {filteredNodes.length} organizations (+{filteredNodes.length - INITIAL_DISPLAY_COUNT} more)
              </button>
            ) : (
              <button className="org-expand-btn" onClick={() => setShowAll(false)}>
                <i className="fas fa-chevron-up"></i>
                Show less
              </button>
            )}
          </div>
        )}

        {/* Backdrop to close panel when clicking outside */}
        {selectedOrg && (
          <div 
            className="org-detail-backdrop"
            onClick={() => setSelectedOrg(null)}
          />
        )}

        {/* Selected Organization Detail - positioned near the bubble */}
        {selectedOrg && (
          <div 
            className="org-detail-panel"
            onClick={(e) => e.stopPropagation()}
            style={{
              left: `${Math.min(selectedPosition.x, containerRef.current?.offsetWidth - 300 || selectedPosition.x)}px`,
              top: `${selectedPosition.y}px`
            }}
          >
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

            <div className="org-detail-projects">
              <h4>
                <i className="fas fa-folder-open"></i>
                {selectedOrg.projectCount} Project{selectedOrg.projectCount !== 1 ? 's' : ''}
              </h4>
              <ul className="org-project-list">
                {selectedOrg.projects.slice(0, 10).map(project => (
                  <li key={project.id}>
                    <a href={`#${project.id}`} className="org-project-link">
                      {project.title}
                    </a>
                  </li>
                ))}
                {selectedOrg.projects.length > 10 && (
                  <li className="org-project-more">
                    +{selectedOrg.projects.length - 10} more projects
                  </li>
                )}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="org-network-legend">
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: '#059669' }}></span>
          <span>Implementers (Powered by)</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: '#6366f1' }}></span>
          <span>Catalysts (Catalyzed by)</span>
        </div>
        <div className="org-legend-item">
          <span className="org-legend-dot" style={{ backgroundColor: '#2563eb' }}></span>
          <span>Financers (Financed by)</span>
        </div>
        <div className="org-legend-size">
          <span className="org-legend-dot-small"></span>
          <span className="org-legend-dot-large"></span>
          <span>Bubble size = project count</span>
        </div>
      </div>
    </div>
  )
}

export default OrganizationNetwork

