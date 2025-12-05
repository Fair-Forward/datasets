import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { withBasePath } from '../utils/basePath'

const normalizeLabel = (value = '') =>
  value
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')

const getDataTypeIcon = (normalized) => {
  if (!normalized) return 'fa-database'

  const iconMap = {
    images: 'fa-images',
    image: 'fa-images',
    'drone-imagery': 'fa-satellite',
    audio: 'fa-microphone',
    voice: 'fa-microphone-lines',
    text: 'fa-file-lines',
    tabular: 'fa-table-cells',
    video: 'fa-film',
    geospatial: 'fa-earth-americas',
    'geospatialremote-sensing': 'fa-earth-americas',
    'geospatial-remote-sensing': 'fa-earth-americas',
    meterological: 'fa-cloud-sun',
    meteorological: 'fa-cloud-sun'
  }

  for (const [key, icon] of Object.entries(iconMap)) {
    if (normalized === key || normalized.startsWith(key)) {
      return icon
    }
  }

  return 'fa-database'
}

const DetailPanel = ({ project, onClose }) => {
  const [markdownContent, setMarkdownContent] = useState({})
  const [loading, setLoading] = useState(true)
  const datasetLinks = project?.dataset_links || []
  const usecaseLinks = project?.usecase_links || []
  const sdgs = project?.sdgs || []
  const dataTypes = project?.data_types || []

  useEffect(() => {
    if (!project) return

    // Reset state on project change
    setLoading(true)
    setMarkdownContent({})

    // Load markdown files
    const loadMarkdown = async () => {
      try {
        const files = {
          description: 'description.md',
          data_characteristics: 'data_characteristics.md',
          model_characteristics: 'model_characteristics.md',
          how_to_use: 'how_to_use.md'
        }

        const content = {}
        
        for (const [key, filename] of Object.entries(files)) {
          try {
            const response = await fetch(withBasePath(`projects/${project.id}/docs/${filename}`))
            if (response.ok) {
              content[key] = await response.text()
            }
          } catch (err) {
            console.log(`Could not load ${filename}:`, err)
          }
        }

        setMarkdownContent(content)
        setLoading(false)
      } catch (err) {
        console.error('Error loading markdown:', err)
        setLoading(false)
      }
    }

    loadMarkdown()
  }, [project])

  if (!project) return null

  return (
    <>
      <div className="panel-overlay active" onClick={onClose}></div>
      <div className="detail-panel open">
        <div className="detail-panel-header">
          <button className="close-panel-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
          <h2>{project.title}</h2>
        </div>
        
        <div className="detail-panel-content">
          {loading ? (
            <div className="panel-loader">
              <div className="loader-spinner"></div>
              <p>Loading details...</p>
            </div>
          ) : (
            <>
              {project.image && (
                <div
                  className="panel-header-image"
                  style={{ backgroundImage: `url("${withBasePath(project.image)}")` }}
                />
              )}

              <div className="panel-title-section">
                {project.sdgs?.length > 0 && (
                  <div className="panel-domain-badges">
                    {project.sdgs.map((sdg) => (
                      <span key={sdg} className="panel-domain-badge">
                        {sdg}
                      </span>
                    ))}
                  </div>
                )}

                {(datasetLinks.length > 0 || usecaseLinks.length > 0) && (
                  <div className="panel-links-section">
                    {datasetLinks.map((link, idx) => (
                      <a
                        key={`dataset-${idx}`}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="panel-link-btn panel-dataset-link"
                      >
                        <i className="fas fa-database"></i>
                        {link.name || `Dataset ${idx + 1}`}
                      </a>
                    ))}
                    {usecaseLinks.map((link, idx) => (
                      <a
                        key={`usecase-${idx}`}
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="panel-link-btn panel-usecase-link"
                      >
                        <i className="fas fa-lightbulb"></i>
                        {link.name || `Use Case ${idx + 1}`}
                      </a>
                    ))}
                  </div>
                )}
              </div>

              {dataTypes.length > 0 && (
                <div className="data-types-container">
                  {dataTypes.map((type) => {
                    const normalized = normalizeLabel(type)
                    const icon = getDataTypeIcon(normalized)
                    return (
                      <div key={type} className={`data-type-item label-${normalized}`}>
                        <div className="data-type-header">
                          <i className={`fas ${icon}`} aria-hidden="true"></i>
                          <span className="data-type-label">{type}</span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              <div className="panel-data active">
                {(markdownContent.description || project?.description) && (
                  <section className="detail-section">
                    <h3 data-section="What is this about and how can I use this?">Description</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>
                        {markdownContent.description || project?.description}
                      </ReactMarkdown>
                    </div>
                  </section>
                )}

                {markdownContent.data_characteristics && (
                  <section className="detail-section">
                    <h3 data-section="Data Characteristics">Data Characteristics</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>{markdownContent.data_characteristics}</ReactMarkdown>
                    </div>
                  </section>
                )}

                {markdownContent.model_characteristics && (
                  <section className="detail-section">
                    <h3 data-section="Model Characteristics">Model / Use Case Characteristics</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>{markdownContent.model_characteristics}</ReactMarkdown>
                    </div>
                  </section>
                )}

                {markdownContent.how_to_use && (
                  <section className="detail-section">
                    <h3 data-section="How to Use It">How to Use</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>{markdownContent.how_to_use}</ReactMarkdown>
                    </div>
                  </section>
                )}

                <section className="detail-section">
                  <h3 data-section="Tags">Metadata</h3>
                  <div className="detail-metadata">
                    {project?.countries?.length > 0 && (
                      <div className="metadata-item">
                        <strong>Countries:</strong> {project.countries.join(', ')}
                      </div>
                    )}
                    {sdgs.length > 0 && (
                      <div className="metadata-item">
                        <strong>SDGs:</strong> {sdgs.join(', ')}
                      </div>
                    )}
                    {dataTypes.length > 0 && (
                      <div className="metadata-item">
                        <strong>Data Types:</strong> {dataTypes.join(', ')}
                      </div>
                    )}
                    {(() => {
                      const rawLicense = project?.license && project.license.trim() ? project.license.trim() : 'cc-by-4.0'
                      const urlMatch = rawLicense.match(/https?:\/\/[^\s)]+/i)
                      let label = rawLicense
                      if (!urlMatch && /^\d+(\.\d+)?$/.test(rawLicense)) {
                        label = `cc-by-${rawLicense}`
                      }
                      if (!rawLicense) return null
                      return (
                        <div className="metadata-item">
                          <strong>License:</strong>{' '}
                          {(() => {
                            if (urlMatch) {
                              const url = urlMatch[0]
                              const text = rawLicense.replace(url, '').trim() || url
                              return (
                                <a href={url} target="_blank" rel="noopener noreferrer">
                                  {text}
                                </a>
                              )
                            }
                            return label.toLowerCase()
                          })()}
                        </div>
                      )
                    })()}
                    {project?.contact && (() => {
                      const cleanLabel = (label = '') =>
                        label
                          .replace(/\([^)]*\)/g, ' ')
                          .replace(/\s{2,}/g, ' ')
                          .trim()

                      const emailMatch = project.contact.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)
                      const urlMatch = project.contact.match(/https?:\/\/[^\s)]+/i)
                      const beforeComma = project.contact.split(',')[0].trim()
                      const beforeParen = project.contact.split('(')[0].trim()
                      const baseLabel = cleanLabel(beforeComma || beforeParen || project.contact)

                      if (emailMatch) {
                        const email = emailMatch[0]
                        const label = cleanLabel(baseLabel.replace(email, '').trim()) || baseLabel || email
                        return (
                          <div className="metadata-item">
                            <strong>Contact:</strong>{' '}
                            <a href={`mailto:${email}`}>{label}</a>
                          </div>
                        )
                      }
                      if (urlMatch) {
                        const url = urlMatch[0]
                        const label = cleanLabel(baseLabel.replace(url, '').trim()) || baseLabel || url
                        return (
                          <div className="metadata-item">
                            <strong>Contact:</strong>{' '}
                            <a href={url} target="_blank" rel="noopener noreferrer">{label}</a>
                          </div>
                        )
                      }
                      return (
                        <div className="metadata-item">
                          <strong>Contact:</strong> {baseLabel}
                        </div>
                      )
                    })()}
                  </div>
                </section>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}

export default DetailPanel

