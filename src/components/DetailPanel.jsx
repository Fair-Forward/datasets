import { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { withBasePath } from '../utils/basePath'

// Build shareable URL for a project
const getShareUrl = (projectId) => {
  const url = new URL(window.location.href)
  url.searchParams.set('project', projectId)
  return url.toString()
}

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

// Extract SDG numbers from SDG labels like "SDG 1", "SDG 15"
const extractSdgNumbers = (sdgs = []) => {
  const numbers = []
  for (const sdg of sdgs) {
    const match = sdg.match(/SDG\s*(\d+)/i)
    if (match) {
      const num = parseInt(match[1], 10)
      if (num >= 1 && num <= 17) {
        numbers.push(num)
      }
    }
  }
  return [...new Set(numbers)].sort((a, b) => a - b)
}

// Parse organizations into Powered by / Catalyzed by / Financed by
const parseOrganizations = (orgText = '') => {
  if (!orgText) return null

  const extractSection = (label) => {
    const pattern = new RegExp(`${label}:\\s*`, 'i')
    const idx = orgText.search(pattern)
    if (idx === -1) return null

    const startIdx = idx + orgText.substring(idx).indexOf(':') + 1
    const remaining = orgText.substring(startIdx)

    const nextLabels = [
      remaining.search(/Catalyzed by:/i),
      remaining.search(/Financed by:/i),
      remaining.search(/Powered by:/i)
    ].filter(i => i >= 0)

    const endIdx = nextLabels.length > 0 ? Math.min(...nextLabels) : remaining.length
    return remaining.substring(0, endIdx).trim()
  }

  const powered = extractSection('Powered by')
  const catalyzed = extractSection('Catalyzed by')
  const financed = extractSection('Financed by')

  if (!powered && !catalyzed && !financed) {
    // No structured format - return raw text
    return { raw: orgText }
  }

  return { powered, catalyzed, financed }
}

const DetailPanel = ({ project, onClose }) => {
  const [markdownContent, setMarkdownContent] = useState({})
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const datasetLinks = project?.dataset_links || []
  const usecaseLinks = project?.usecase_links || []
  const isOnHold = Boolean(project?.is_on_hold)
  const hasLinks = datasetLinks.length > 0 || usecaseLinks.length > 0
  const sdgs = project?.sdgs || []
  const dataTypes = project?.data_types || []
  const sdgNumbers = extractSdgNumbers(sdgs)
  const organizations = parseOrganizations(project?.organizations)

  const handleShare = useCallback(async () => {
    const url = getShareUrl(project.id)
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      window.prompt('Copy this link:', url)
    }
  }, [project?.id])

  useEffect(() => {
    if (!project) return

    setLoading(true)
    setMarkdownContent({})

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

  // Build TOC entries
  const tocSections = []
  if (markdownContent.description || project?.description) {
    tocSections.push({ id: 'description', label: 'What is this about?', icon: 'fa-circle-info' })
  }
  if (markdownContent.data_characteristics || dataTypes.length > 0) {
    tocSections.push({ id: 'data-characteristics', label: 'Data Characteristics', icon: 'fa-database' })
  }
  if (markdownContent.model_characteristics?.trim()) {
    tocSections.push({ id: 'model-characteristics', label: 'Model Characteristics', icon: 'fa-robot' })
  }
  if (markdownContent.how_to_use) {
    tocSections.push({ id: 'how-to-use', label: 'How to Use It', icon: 'fa-lightbulb' })
  }
  if (organizations) {
    tocSections.push({ id: 'organizations', label: 'Organizations Involved', icon: 'fa-building' })
  }
  if (project?.countries?.length > 0) {
    tocSections.push({ id: 'region', label: 'Region', icon: 'fa-location-dot' })
  }
  // if (project?.authors) {
  //   tocSections.push({ id: 'authors', label: 'Authors', icon: 'fa-user-pen' })
  // }

  return (
    <>
      <div className="panel-overlay active" onClick={onClose}></div>
      <div className="detail-panel open">
        <div className="detail-panel-header">
          <div className="detail-panel-header-actions">
            <button 
              className="share-panel-btn" 
              onClick={handleShare}
              title={copied ? 'Link copied!' : 'Copy link to share'}
            >
              <i className={`fas ${copied ? 'fa-check' : 'fa-share-nodes'}`}></i>
            </button>
            <button className="close-panel-btn" onClick={onClose}>
              <i className="fas fa-times"></i>
            </button>
          </div>
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
              {/* Header Image */}
              {project.image && (
                <div
                  className="panel-header-image"
                  style={{ backgroundImage: `url("${withBasePath(project.image)}")` }}
                />
              )}

              {/* Title Section with Badges and Links */}
              <div className="panel-title-section">
                {sdgs.length > 0 && (
                  <div className="panel-domain-badges">
                    {sdgs.map((sdg) => (
                      <span key={sdg} className="panel-domain-badge">
                        {sdg}
                      </span>
                    ))}
                  </div>
                )}

                {/* Links Section */}
                <div className="panel-links-section">
                  {isOnHold ? (
                    <div className="panel-on-hold-note">
                      <i className="fas fa-info-circle"></i>
                      Note: This project is active, but the link is temporarily unavailable (e.g., due to migration).
                    </div>
                  ) : (
                    <>
                      {datasetLinks.map((link, idx) => (
                        <a
                          key={`dataset-${idx}`}
                          href={link.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="panel-link-btn panel-dataset-link"
                        >
                          <i className="fas fa-cloud-arrow-down"></i>
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
                          <i className="fas fa-sparkles"></i>
                          {link.name || `Use Case ${idx + 1}`}
                        </a>
                      ))}
                    </>
                  )}
                </div>
              </div>

              {/* Table of Contents */}
              {tocSections.length > 1 && (
                <div className="panel-toc">
                  <div className="panel-toc-title">
                    <i className="fas fa-list"></i> Contents
                  </div>
                  <ul className="panel-toc-list">
                    {tocSections.map((section) => (
                      <li key={section.id} className="panel-toc-item">
                        <a href={`#${section.id}`} className="panel-toc-link">
                          <i className={`fas ${section.icon}`}></i> {section.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="panel-data active">
                {/* Description Section with SDG Icons */}
                {(markdownContent.description || project?.description) && (
                  <section className="detail-section" id="description">
                    <h3 data-section="What is this about and how can I use this?">What is this about?</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>
                        {markdownContent.description || project?.description}
                      </ReactMarkdown>
                    </div>
                    {sdgNumbers.length > 0 && (
                      <div className="sdg-icons-container">
                        {sdgNumbers.map((num) => (
                          <img
                            key={num}
                            src={withBasePath(`img/sdg-${num}.png`)}
                            alt={`SDG ${num}`}
                            className="sdg-icon"
                            onError={(e) => { e.target.style.display = 'none' }}
                          />
                        ))}
                      </div>
                    )}
                  </section>
                )}

                {/* Data Characteristics Section with Data Types at Top */}
                {(markdownContent.data_characteristics || dataTypes.length > 0) && (
                  <section className="detail-section" id="data-characteristics">
                    <h3 data-section="Data Characteristics">Data Characteristics</h3>
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
                    {markdownContent.data_characteristics && (
                      <div className="detail-content documentation-content">
                        <ReactMarkdown>{markdownContent.data_characteristics}</ReactMarkdown>
                      </div>
                    )}
                  </section>
                )}

                {/* Model Characteristics Section */}
                {markdownContent.model_characteristics?.trim() && (
                  <section className="detail-section" id="model-characteristics">
                    <h3 data-section="Model Characteristics">Model / Use Case Characteristics</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>{markdownContent.model_characteristics}</ReactMarkdown>
                    </div>
                  </section>
                )}

                {/* How to Use Section */}
                {markdownContent.how_to_use && (
                  <section className="detail-section" id="how-to-use">
                    <h3 data-section="How to Use It">How to Use It</h3>
                    <div className="detail-content documentation-content">
                      <ReactMarkdown>{markdownContent.how_to_use}</ReactMarkdown>
                    </div>
                  </section>
                )}

                {/* Organizations Involved Section */}
                {organizations && (
                  <section className="detail-section" id="organizations">
                    <h3 data-section="Organizations Involved">Organizations Involved</h3>
                    {organizations.raw ? (
                      <div className="documentation-content">
                        <ReactMarkdown>{organizations.raw}</ReactMarkdown>
                      </div>
                    ) : (
                      <div className="organizations-container">
                        {organizations.powered && (
                          <div className="org-type org-powered">
                            <div className="org-type-header">
                              <i className="fas fa-rocket"></i>
                              <span className="org-type-label">Powered by</span>
                            </div>
                            <div className="org-type-content">
                              <ReactMarkdown>{organizations.powered}</ReactMarkdown>
                            </div>
                          </div>
                        )}
                        {organizations.catalyzed && (
                          <div className="org-type org-catalyzed">
                            <div className="org-type-header">
                              <i className="fas fa-seedling"></i>
                              <span className="org-type-label">Catalyzed by</span>
                            </div>
                            <div className="org-type-content">
                              <ReactMarkdown>{organizations.catalyzed}</ReactMarkdown>
                            </div>
                          </div>
                        )}
                        {organizations.financed && (
                          <div className="org-type org-financed">
                            <div className="org-type-header">
                              <i className="fas fa-coins"></i>
                              <span className="org-type-label">Financed by</span>
                            </div>
                            <div className="org-type-content">
                              <ReactMarkdown>{organizations.financed}</ReactMarkdown>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </section>
                )}

                {/* Region Section */}
                {project?.countries?.length > 0 && (
                  <section className="detail-section" id="region">
                    <h3 data-section="Region">Region</h3>
                    <div className="documentation-content">
                      <p><i className="fas fa-location-dot"></i> {project.countries.join(', ')}</p>
                    </div>
                  </section>
                )}

                {/* Authors Section */}
                {project?.authors && (
                  <section className="detail-section" id="authors">
                    <h3 data-section="Authors">Authors</h3>
                    <div className="documentation-content">
                      <ReactMarkdown>{project.authors}</ReactMarkdown>
                    </div>
                  </section>
                )}

                {/* Tags Section (License + Contact) */}
                <section className="detail-section" id="tags">
                  <h3 data-section="Tags">Tags</h3>
                  <div className="documentation-content tags-content">
                    {(() => {
                      const rawLicense = project?.license?.trim() || 'cc-by-4.0'
                      const urlMatch = rawLicense.match(/https?:\/\/[^\s)]+/i)
                      let label = rawLicense
                      if (!urlMatch && /^\d+(\.\d+)?$/.test(rawLicense)) {
                        label = `cc-by-${rawLicense}`
                      }
                      return (
                        <div className="tag-item">
                          <i className="fas fa-copyright"></i>
                          <strong>License:</strong>{' '}
                          {urlMatch ? (
                            <a href={urlMatch[0]} target="_blank" rel="noopener noreferrer">
                              {rawLicense.replace(urlMatch[0], '').trim() || urlMatch[0]}
                            </a>
                          ) : (
                            label.toLowerCase()
                          )}
                        </div>
                      )
                    })()}
                    {project?.contact && (() => {
                      const cleanLabel = (label = '') =>
                        label.replace(/\([^)]*\)/g, ' ').replace(/\s{2,}/g, ' ').trim()

                      const emailMatch = project.contact.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)
                      const urlMatch = project.contact.match(/https?:\/\/[^\s)]+/i)
                      const beforeComma = project.contact.split(',')[0].trim()
                      const beforeParen = project.contact.split('(')[0].trim()
                      const baseLabel = cleanLabel(beforeComma || beforeParen || project.contact)

                      if (emailMatch) {
                        const email = emailMatch[0]
                        const label = cleanLabel(baseLabel.replace(email, '').trim()) || baseLabel || email
                        return (
                          <div className="tag-item">
                            <i className="fas fa-envelope"></i>
                            <strong>Contact:</strong>{' '}
                            <a href={`mailto:${email}`}>{label}</a>
                          </div>
                        )
                      }
                      if (urlMatch) {
                        const url = urlMatch[0]
                        const label = cleanLabel(baseLabel.replace(url, '').trim()) || baseLabel || url
                        return (
                          <div className="tag-item">
                            <i className="fas fa-link"></i>
                            <strong>Contact:</strong>{' '}
                            <a href={url} target="_blank" rel="noopener noreferrer">{label}</a>
                          </div>
                        )
                      }
                      return (
                        <div className="tag-item">
                          <i className="fas fa-user"></i>
                          <strong>Contact:</strong> {baseLabel}
                        </div>
                      )
                    })()}
                    {sdgs.length > 0 && (
                      <div className="tag-item">
                        <i className="fas fa-bullseye"></i>
                        <strong>SDGs:</strong> {sdgs.join(', ')}
                      </div>
                    )}
                    {dataTypes.length > 0 && (
                      <div className="tag-item">
                        <i className="fas fa-database"></i>
                        <strong>Data Types:</strong> {dataTypes.join(', ')}
                      </div>
                    )}
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
