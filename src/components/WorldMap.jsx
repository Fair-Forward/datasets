import { useState, useEffect, useMemo, memo } from 'react'
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup
} from 'react-simple-maps'
import { Tooltip } from 'react-tooltip'
import { scaleLinear } from 'd3-scale'
import { interpolateHcl } from 'd3-interpolate'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

// Custom name normalization for matching
const NAME_OVERRIDES = {
  'Democratic Republic of the Congo': 'CD',
  'Dem. Rep. Congo': 'CD',
  'Republic of the Congo': 'CG',
  'Congo': 'CG',
  'Ivory Coast': 'CI',
  "Côte d'Ivoire": 'CI',
  'Myanmar': 'MM',
  'Burma': 'MM',
  'United States of America': 'US',
  'United Kingdom': 'GB',
  'Cape Verde': 'CV',
  'Equatorial Guinea': 'GQ',
  'Guinea-Bissau': 'GW',
  'eSwatini': 'SZ',
  'Swaziland': 'SZ',
  'South Sudan': 'SS',
  'Central African Rep.': 'CF',
  'Central African Republic': 'CF',
  'S. Sudan': 'SS',
  'Eq. Guinea': 'GQ',
  'W. Sahara': 'EH',
  'Western Sahara': 'EH',
  'Somaliland': 'SO',
  'Tanzania': 'TZ',
  'United Republic of Tanzania': 'TZ'
}

const normalizeName = (value = '') =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z]/gi, '')
    .toLowerCase()

// Warm color palette - orange/amber that pops against light gray
const COLOR_CONFIG = {
  empty: '#f1f5f9',           // Light gray for empty countries
  emptyHover: '#e2e8f0',      // Slightly darker on hover
  emptyStroke: '#e2e8f0',     // Very subtle border for empty
  dataStroke: '#c2410c',      // Strong orange border for countries with data
  strokeHighlight: '#ea580c', // Bright orange for selected
  gradientStart: '#fed7aa',   // Light peach/orange
  gradientMid: '#fb923c',     // Medium orange
  gradientEnd: '#c2410c',     // Deep burnt orange for high values
  ocean: '#f8fafc'            // Very light for ocean/background
}

const WorldMap = ({
  projectData,
  width = 960,
  height = 500,
  onCountryClick,
  selectedCountry = null,
  filters = {} // For future filter support
}) => {
  const [tooltipContent, setTooltipContent] = useState('')
  const [position, setPosition] = useState({ coordinates: [20, 5], zoom: 1.2 })
  const [geoData, setGeoData] = useState(null)

  // Load geography data
  useEffect(() => {
    fetch(GEO_URL)
      .then(res => res.json())
      .then(data => setGeoData(data))
      .catch(err => console.error('Failed to load map data:', err))
  }, [])

  // Build lookup maps
  const { dataByIso, dataByName, maxValue, minValue } = useMemo(() => {
    const entries = Object.values(projectData || {})
    const byIso = new Map()
    const byName = new Map()
    let max = 0
    let min = Infinity

    entries.forEach((entry) => {
      if (!entry) return
      const iso = entry.iso2?.toUpperCase()
      const name = entry.name
      const value = typeof entry.projects === 'number' ? entry.projects : 0
      
      if (iso) byIso.set(iso, entry)
      if (name) {
        byName.set(normalizeName(name), entry)
        byName.set(name, entry)
      }
      
      if (value > max) max = value
      if (value > 0 && value < min) min = value
    })

    return {
      dataByIso: byIso,
      dataByName: byName,
      maxValue: max || 1,
      minValue: min === Infinity ? 0 : min
    }
  }, [projectData])

  // Color scale using warm orange gradient
  const colorScale = useMemo(() => {
    return scaleLinear()
      .domain([0, maxValue * 0.3, maxValue])
      .range([COLOR_CONFIG.gradientStart, COLOR_CONFIG.gradientMid, COLOR_CONFIG.gradientEnd])
      .interpolate(interpolateHcl)
  }, [maxValue])

  // Lookup country data from geography
  const getCountryData = (geo) => {
    const props = geo.properties || {}
    
    // Try ISO code first
    const isoA2 = props.ISO_A2 || props.iso_a2
    if (isoA2 && dataByIso.has(isoA2)) {
      return dataByIso.get(isoA2)
    }

    // Try name override
    const name = props.name || props.NAME
    if (name && NAME_OVERRIDES[name]) {
      const iso = NAME_OVERRIDES[name]
      if (dataByIso.has(iso)) {
        return dataByIso.get(iso)
      }
    }
    
    // Try normalized name match
    if (name) {
      const normalized = normalizeName(name)
      if (dataByName.has(normalized)) {
        return dataByName.get(normalized)
      }
      if (dataByName.has(name)) {
        return dataByName.get(name)
    }
    }
    
    return null
  }

  const handleMouseEnter = (geo, countryData) => {
    const name = geo.properties?.name || geo.properties?.NAME || 'Unknown'
    
    if (countryData) {
      const sdgList = countryData.sdgs?.slice(0, 4).join(', ') || ''
      const moreSDGs = countryData.sdgs?.length > 4 ? ` +${countryData.sdgs.length - 4} more` : ''
      const dataTypes = countryData.data_types?.slice(0, 2).join(', ') || ''
      const moreTypes = countryData.data_types?.length > 2 ? ` +${countryData.data_types.length - 2}` : ''
      
      setTooltipContent(`
        <div class="map-tooltip">
          <div class="map-tooltip-title">${countryData.name}</div>
          <div class="map-tooltip-stat">
            <span class="map-tooltip-value">${countryData.projects}</span>
            <span class="map-tooltip-label">project${countryData.projects !== 1 ? 's' : ''}</span>
          </div>
          ${sdgList ? `<div class="map-tooltip-detail"><span class="map-tooltip-icon">🎯</span>${sdgList}${moreSDGs}</div>` : ''}
          ${dataTypes ? `<div class="map-tooltip-detail"><span class="map-tooltip-icon">📊</span>${dataTypes}${moreTypes}</div>` : ''}
          <div class="map-tooltip-hint">Click for details</div>
        </div>
      `)
    } else {
      setTooltipContent(`
        <div class="map-tooltip">
          <div class="map-tooltip-title">${name}</div>
          <div class="map-tooltip-empty">No projects yet</div>
        </div>
      `)
      }
  }

  const handleMouseLeave = () => {
    setTooltipContent('')
  }

  const handleClick = (geo) => {
    const countryData = getCountryData(geo)
    if (onCountryClick) {
      // If country has data, select it. If not, deselect (pass null)
      onCountryClick(countryData && countryData.projects > 0 ? countryData : null)
    }
  }

  const handleBackgroundClick = (e) => {
    // Only deselect if clicking directly on the SVG background (not a country)
    if (e.target.tagName === 'svg' || e.target.tagName === 'rect') {
      if (onCountryClick) {
        onCountryClick(null)
            }
          }
  }

  const handleZoomIn = () => {
    if (position.zoom < 4) {
      setPosition(pos => ({ ...pos, zoom: pos.zoom * 1.5 }))
    }
  }

  const handleZoomOut = () => {
    if (position.zoom > 1) {
      setPosition(pos => ({ ...pos, zoom: pos.zoom / 1.5 }))
    }
  }

  const handleReset = () => {
    setPosition({ coordinates: [20, 5], zoom: 1.2 })
  }

  if (!geoData) {
    return (
      <div className="map-loading">
        <div className="map-loading-spinner"></div>
        <span>Loading map data...</span>
      </div>
    )
  }

  return (
    <div className="world-map-wrapper">
      <div className="map-controls">
        <button onClick={handleZoomIn} className="map-control-btn" title="Zoom in">
          <i className="fas fa-plus"></i>
        </button>
        <button onClick={handleZoomOut} className="map-control-btn" title="Zoom out">
          <i className="fas fa-minus"></i>
        </button>
        <button onClick={handleReset} className="map-control-btn" title="Reset view">
          <i className="fas fa-expand"></i>
        </button>
      </div>

      <ComposableMap
        data-tooltip-id="map-tooltip"
        data-tooltip-html={tooltipContent}
        projection="geoMercator"
        projectionConfig={{
          scale: 140,
          center: [20, 5]
        }}
        onClick={handleBackgroundClick}
      style={{
        width: '100%',
          height: 'auto',
          maxHeight: '500px',
          backgroundColor: COLOR_CONFIG.ocean
        }}
      >
        <ZoomableGroup
          zoom={position.zoom}
          center={position.coordinates}
          onMoveEnd={setPosition}
          minZoom={1}
          maxZoom={6}
        >
          <Geographies geography={geoData}>
            {({ geographies }) =>
              geographies.map((geo) => {
                const countryData = getCountryData(geo)
                const isSelected = selectedCountry?.iso2 === countryData?.iso2
                const hasData = countryData && countryData.projects > 0
                
                return (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    onMouseEnter={() => handleMouseEnter(geo, countryData)}
                    onMouseLeave={handleMouseLeave}
                    onClick={() => handleClick(geo)}
                    style={{
                      default: {
                        fill: hasData ? colorScale(countryData.projects) : COLOR_CONFIG.empty,
                        stroke: hasData ? COLOR_CONFIG.dataStroke : COLOR_CONFIG.emptyStroke,
                        strokeWidth: hasData ? 1.2 : 0.3,
                        outline: 'none',
                        transition: 'all 0.2s ease-out',
                        filter: isSelected ? 'drop-shadow(0 0 4px rgba(194, 65, 12, 0.5))' : 'none'
                      },
                      hover: {
                        fill: hasData ? colorScale(countryData.projects) : COLOR_CONFIG.emptyHover,
                        stroke: hasData ? COLOR_CONFIG.strokeHighlight : COLOR_CONFIG.emptyStroke,
                        strokeWidth: hasData ? 2 : 0.5,
                        outline: 'none',
                        cursor: hasData ? 'pointer' : 'default',
                        filter: hasData ? 'brightness(1.05) drop-shadow(0 0 6px rgba(194, 65, 12, 0.4))' : 'none'
                      },
                      pressed: {
                        fill: hasData ? colorScale(countryData.projects) : COLOR_CONFIG.emptyHover,
                        stroke: COLOR_CONFIG.strokeHighlight,
                        strokeWidth: 2,
                        outline: 'none'
                      }
                    }}
                  />
                )
              })
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>

      <Tooltip
        id="map-tooltip"
        className="map-tooltip-container"
        place="top"
        opacity={1}
        style={{
          backgroundColor: 'transparent',
          padding: 0,
          zIndex: 1000
        }}
      />

      {/* Legend */}
      <div className="map-legend">
        <div className="map-legend-title">Projects</div>
        <div className="map-legend-gradient">
          <div 
            className="map-legend-bar"
            style={{
              background: `linear-gradient(to right, ${COLOR_CONFIG.gradientStart}, ${COLOR_CONFIG.gradientMid}, ${COLOR_CONFIG.gradientEnd})`
      }}
    />
          <div className="map-legend-labels">
            <span>1</span>
            <span>{Math.round(maxValue / 2)}</span>
            <span>{maxValue}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default memo(WorldMap)
