import { useRef, useEffect, useMemo, useState, useCallback } from 'react'
import * as Plot from '@observablehq/plot'
import * as topojson from 'topojson-client'

const NAME_OVERRIDES = {
  democraticrepublicofthecongo: 'CD',
  republicofthecongo: 'CG',
  congobrazzaville: 'CG',
  congokinshasa: 'CD',
  ivorycoast: 'CI',
  cotedivoire: 'CI',
  myanmar: 'MM',
  burma: 'MM',
  unitedstatesofamerica: 'US',
  unitedkingdom: 'GB',
  capeverde: 'CV',
  equatorialguinea: 'GQ',
  guineabissau: 'GW'
}

const normalizeName = (value = '') =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z]/gi, '')
    .toLowerCase()

const WorldMap = ({
  projectData,
  width = 960,
  height = 480,
  metricKey = 'projects',
  metricLabel = 'Projects',
  colorScheme = 'Blues',
  onCountryClick
}) => {
  const containerRef = useRef()
  const [worldData, setWorldData] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState(null)

  const { dataByIso, dataByName, maxValue } = useMemo(() => {
    const entries = Object.values(projectData || {})
    const byIso = new Map()
    const byName = new Map()
    let max = 0

    entries.forEach((entry) => {
      if (!entry) return
      const iso = entry.iso2?.toUpperCase()
      const normalizedName = normalizeName(entry.name)
      const value = typeof entry[metricKey] === 'number' ? entry[metricKey] : 0
      if (iso) byIso.set(iso, entry)
      if (normalizedName) byName.set(normalizedName, entry)
      if (value > max) max = value
    })

    return {
      dataByIso: byIso,
      dataByName: byName,
      maxValue: max || 1
    }
  }, [projectData, metricKey])

  const lookupCountryData = useCallback((feature) => {
    if (!feature) return null

    const isoCandidate =
      feature.properties?.iso_a2?.toUpperCase() ||
      (typeof feature.id === 'string' && feature.id.length === 2 ? feature.id.toUpperCase() : null)

    if (isoCandidate && dataByIso.has(isoCandidate)) {
      return dataByIso.get(isoCandidate)
    }

    const normalizedName = normalizeName(feature.properties?.name || '')
    if (!normalizedName) return null

    const overrideIso = NAME_OVERRIDES[normalizedName]
    if (overrideIso && dataByIso.has(overrideIso)) {
      return dataByIso.get(overrideIso)
    }

    if (dataByName.has(normalizedName)) {
      return dataByName.get(normalizedName)
    }
    return null
  }, [dataByIso, dataByName])

  // Load world topology data once
  useEffect(() => {
    let cancelled = false
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json')
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled) setWorldData(data)
      })
      .catch((error) => {
        console.error('Error loading world map:', error)
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Create the map when data is available
  useEffect(() => {
    if (!worldData || !containerRef.current) return

    const countries = topojson.feature(worldData, worldData.objects.countries)

    const plot = Plot.plot({
      width,
      height,
      projection: 'equal-earth',
      style: { background: 'transparent', cursor: 'pointer' },
      marks: [
        Plot.geo(countries, {
          fill: (d) => {
            const countryData = lookupCountryData(d)
            return countryData ? countryData[metricKey] || 0 : 0
          },
          stroke: '#94a3b8',
          strokeWidth: 0.5,
          title: (d) => {
            const countryData = lookupCountryData(d)
            if (countryData) {
              const value = countryData[metricKey] || 0
              const sdgs = countryData.sdgs?.length > 0 
                ? `\nSDGs: ${countryData.sdgs.join(', ')}`
                : ''
              const dataTypes = countryData.data_types?.length > 0
                ? `\nData: ${countryData.data_types.slice(0, 3).join(', ')}${countryData.data_types.length > 3 ? '...' : ''}`
                : ''
              return `${countryData.name}\n${value} ${metricLabel.toLowerCase()}${sdgs}${dataTypes}\n\nClick for details`
            }
            return d.properties?.name || 'Unknown country'
          },
          tip: true
        })
      ],
      color: {
        type: 'linear',
        scheme: colorScheme,
        domain: [0, maxValue],
        unknown: '#f1f5f9',
        label: `Number of ${metricLabel}`,
        legend: true
      }
    })

    // Add click handler
    const svg = plot.querySelector('svg')
    if (svg) {
      svg.addEventListener('click', (event) => {
        const target = event.target
        if (target.tagName === 'path') {
          // Find the country data from the path
          const paths = svg.querySelectorAll('path')
          const index = Array.from(paths).indexOf(target)
          if (index >= 0 && countries.features[index]) {
            const feature = countries.features[index]
            const countryData = lookupCountryData(feature)
            if (countryData && onCountryClick) {
              onCountryClick(countryData)
              setSelectedCountry(countryData)
            }
          }
        }
      })
    }

    containerRef.current.innerHTML = ''
    containerRef.current.appendChild(plot)

    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [worldData, width, height, lookupCountryData, maxValue, metricKey, metricLabel, colorScheme, onCountryClick])

  if (!worldData) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-light)' }}>
        Loading map...
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}
    />
  )
}

export default WorldMap

