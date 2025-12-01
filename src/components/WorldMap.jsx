import { useRef, useEffect, useState } from 'react'
import * as Plot from '@observablehq/plot'
import * as topojson from 'topojson-client'

const WorldMap = ({ projectData, width = 1000, height = 550 }) => {
  const containerRef = useRef()
  const [worldData, setWorldData] = useState(null)

  // Load world topology data
  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json')
      .then(res => res.json())
      .then(setWorldData)
      .catch(error => {
        console.error('Error loading world map:', error)
      })
  }, [])

  // Create the map when data is available
  useEffect(() => {
    if (!worldData || !projectData || !containerRef.current) return

    // Convert TopoJSON to GeoJSON
    const countries = topojson.feature(worldData, worldData.objects.countries)

    // Find max value for color scale
    const maxProjects = Math.max(...Object.values(projectData).map(d => d.projects || 0))

    // Create the plot
    const plot = Plot.plot({
      width,
      height,
      projection: 'equal-earth',
      style: {
        background: 'transparent'
      },
      marks: [
        Plot.geo(countries, {
          fill: d => {
            const countryData = projectData[d.properties?.iso_a2]
            return countryData ? countryData.projects : 0
          },
          stroke: '#fff',
          strokeWidth: 0.5,
          title: d => {
            const countryData = projectData[d.properties?.iso_a2]
            if (countryData) {
              return `${countryData.name}: ${countryData.projects} project${countryData.projects > 1 ? 's' : ''}`
            }
            return d.properties.name
          },
          tip: true
        })
      ],
      color: {
        type: 'linear',
        scheme: 'Blues',
        domain: [0, maxProjects],
        unknown: '#e5e7eb',
        label: 'Number of Projects',
        legend: true
      }
    })

    // Clear container and add plot
    containerRef.current.innerHTML = ''
    containerRef.current.appendChild(plot)

    // Cleanup
    return () => {
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [worldData, projectData, width, height])

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

