import { useState, useEffect, useCallback, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { withBasePath, resolvePublicHref } from '../utils/basePath'
import { SDG_COLORS } from '../utils/sdgColors'
import { parseContact, licenseLabel, firstUrl } from '../utils/parsing'

const markdownLinkComponents = {
  a: ({ href, children, ...props }) => {
    const resolved = resolvePublicHref(href)
    const external =
      href &&
      (href.startsWith('http://') || href.startsWith('https://'))
    return (
      <a
        href={resolved}
        {...props}
        target={external ? '_blank' : undefined}
        rel={external ? 'noopener noreferrer' : undefined}
      >
        {children}
      </a>
    )
  }
}

const DocMarkdown = ({ children }) => (
  <ReactMarkdown components={markdownLinkComponents}>{children}</ReactMarkdown>
)

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
  const panelRef = useRef(null)
  const previousFocusRef = useRef(null)
  const datasetLinks = project?.dataset_links || []
  const usecaseLinks = project?.usecase_links || []
  const additionalResources = project?.additional_resources || []
  const hasHttpDatasetOrUsecaseLinks =
    datasetLinks.length > 0 || usecaseLinks.length > 0
  const hasAccessNote =
    Boolean(project?.has_access_note) && !hasHttpDatasetOrUsecaseLinks
  const accessNoteMarkdownTrimmed = (project?.access_note_markdown || '').trim()
  const showAccessCallout = hasAccessNote && accessNoteMarkdownTrimmed.length > 0
  const hostedDocuments = project?.hosted_documents || []
  const showHostedDocuments = hasAccessNote && hostedDocuments.length > 0
  const accessNoteIconClass =
    project?.access_note_kind === 'pending'
      ? 'fa-clock'
      : project?.access_note_kind === 'documents'
        ? 'fa-folder-open'
        : 'fa-circle-info'
  const sdgs = project?.sdgs || []
  const dataTypes = project?.data_types || []
  const sdgNumbers = extractSdgNumbers(sdgs)
  const organizations = parseOrganizations(project?.organizations)

  // Compute license value for metadata grid
  const rawLicense = project?.license?.trim()
  const licenseValue = rawLicense || null

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

  // Focus management and focus trap
  useEffect(() => {
    if (!project) return
    previousFocusRef.current = document.activeElement
    const timer = setTimeout(() => {
      const closeBtn = panelRef.current?.querySelector('.close-panel-btn')
      closeBtn?.focus()
    }, 100)

    const handleKeyDown = (e) => {
      if (e.key === 'Tab' && panelRef.current) {
        const focusable = panelRef.current.querySelectorAll(
          'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        if (focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      clearTimeout(timer)
      previousFocusRef.current?.focus()
    }
  }, [project])

  if (!project) return null

  // Determine primary CTA link
  const primaryLink = datasetLinks[0] || usecaseLinks[0] || null
  const isPrimaryDataset = Boolean(datasetLinks[0])
  // Additional links beyond the primary
  const additionalLinks = [
    ...datasetLinks.slice(isPrimaryDataset ? 1 : 0).map((l, i) => ({ ...l, type: 'dataset', idx: isPrimaryDataset ? i + 1 : i })),
    ...usecaseLinks.slice(isPrimaryDataset ? 0 : 1).map((l, i) => ({ ...l, type: 'usecase', idx: i }))
  ]

  const additionalResourceLinks = additionalResources.filter(r => r.url)

  // Render contact value as JSX using shared parsing
  const renderContact = (contact) => {
    const { label, href } = parseContact(contact)
    if (href && href.startsWith('mailto:')) {
      return <a href={href}>{label}</a>
    }
    if (href) {
      return <a href={href} target="_blank" rel="noopener noreferrer">{label}</a>
    }
    return label
  }

  // Render license value as JSX using shared parsing
  const renderLicense = (raw) => {
    const url = firstUrl(raw)
    const label = licenseLabel(raw)
    if (url) {
      return <a href={url} target="_blank" rel="noopener noreferrer">{label}</a>
    }
    return label
  }

  return (
    <>
      <div className="panel-overlay active" onClick={onClose}></div>
      <div className="detail-panel open" ref={panelRef} role="dialog" aria-modal="true" aria-label={project.title}>
        <div className="detail-panel-header">
          <div className="detail-panel-header-actions">
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
              {/* A) Action Row */}
              <div className="panel-actions">
                {primaryLink ? (() => {
                  const external =
                    primaryLink.url &&
                    (primaryLink.url.startsWith('http://') ||
                      primaryLink.url.startsWith('https://'))
                  return (
                    <a
                      className="panel-cta"
                      href={resolvePublicHref(primaryLink.url)}
                      target={external ? '_blank' : undefined}
                      rel={external ? 'noopener noreferrer' : undefined}
                    >
                      <i className="fas fa-download"></i>
                      {isPrimaryDataset ? 'Access Dataset' : 'Access Use Case'}
                    </a>
                  )
                })() : showHostedDocuments ? (
                  hostedDocuments.map((doc, idx) => {
                    const isPdf = doc.url?.toLowerCase().endsWith('.pdf')
                    return (
                      <a
                        key={`hosted-cta-${idx}`}
                        className="panel-cta"
                        href={resolvePublicHref(doc.url)}
                      >
                        <i className={`fas ${isPdf ? 'fa-file-pdf' : 'fa-file-arrow-down'}`}></i>
                        {doc.name || 'Download Document'}
                      </a>
                    )
                  })
                ) : showAccessCallout ? (
                  <div
                    className={`panel-access-note panel-access-note-${project.access_note_kind || 'unavailable'}`}
                  >
                    <i className={`fas ${accessNoteIconClass}`}></i>
                    <div className="panel-access-note-body documentation-content">
                      <DocMarkdown>{project.access_note_markdown}</DocMarkdown>
                    </div>
                  </div>
                ) : null}
                <button
                  className="panel-action-secondary"
                  onClick={handleShare}
                  title={copied ? 'Link copied!' : 'Copy link to share'}
                >
                  <i className={`fas ${copied ? 'fa-check' : 'fa-arrow-up-right-from-square'}`}></i>
                  {copied ? 'Copied!' : 'Share'}
                </button>
              </div>

              {/* Access note context (shown below documents CTA) */}
              {showHostedDocuments && showAccessCallout && (
                <div className={`panel-access-note panel-access-note-${project.access_note_kind || 'unavailable'}`}>
                  <i className={`fas ${accessNoteIconClass}`}></i>
                  <div className="panel-access-note-body documentation-content">
                    <DocMarkdown>{project.access_note_markdown}</DocMarkdown>
                  </div>
                </div>
              )}

              {/* B) Inline meta row: SDG badges + license */}
              {(sdgs.length > 0 || licenseValue) && (
                <div className="panel-inline-meta">
                  {sdgs.map((sdg) => (
                    <span key={sdg} className="panel-domain-badge">
                      {sdg}
                    </span>
                  ))}
                  {licenseValue && (
                    <span className="license-inline">
                      <i className="fas fa-copyright"></i> {renderLicense(licenseValue)}
                    </span>
                  )}
                </div>
              )}

              {/* C) Hero Image */}
              {(() => {
                if (project.image) {
                  return (
                    <div
                      className="panel-header-image"
                      style={{ backgroundImage: `url("${withBasePath(project.image)}")` }}
                    />
                  )
                }
                const sdgMatch = sdgs.length > 0 && sdgs[0].match(/\d+/)
                const sdgColor = sdgMatch ? SDG_COLORS[parseInt(sdgMatch[0], 10)] : null
                if (sdgColor) {
                  return (
                    <div
                      className="panel-header-image no-image"
                      style={{ backgroundImage: `linear-gradient(135deg, ${sdgColor}18 0%, ${sdgColor}35 100%)` }}
                    />
                  )
                }
                return null
              })()}

              {/* D) Flat content sections */}
              <div className="panel-data active">
                {/* Description Section with SDG Icons */}
                {(markdownContent.description || project?.description) && (
                  <section className="detail-section" id="description">
                    <h3>What is this about?</h3>
                    <div className="detail-content documentation-content">
                      <DocMarkdown>
                        {markdownContent.description || project?.description}
                      </DocMarkdown>
                    </div>
                  </section>
                )}

                {/* Data Characteristics Section with Data Types at Top */}
                {(markdownContent.data_characteristics || dataTypes.length > 0) && (
                  <section className="detail-section" id="data-characteristics">
                    <h3>Data Characteristics</h3>
                    {dataTypes.length > 0 && (
                      <div className="data-type-chips">
                        {dataTypes.map((type) => {
                          const normalized = normalizeLabel(type)
                          const icon = getDataTypeIcon(normalized)
                          return (
                            <span key={type} className="data-type-chip-inline">
                              <i className={`fas ${icon}`} aria-hidden="true"></i> {type}
                            </span>
                          )
                        })}
                      </div>
                    )}
                    {markdownContent.data_characteristics && (
                      <div className="detail-content documentation-content">
                        <DocMarkdown>{markdownContent.data_characteristics}</DocMarkdown>
                      </div>
                    )}
                  </section>
                )}

                {/* Model Characteristics Section */}
                {markdownContent.model_characteristics?.trim() && (
                  <section className="detail-section" id="model-characteristics">
                    <h3>Model / Use Case Characteristics</h3>
                    <div className="detail-content documentation-content">
                      <DocMarkdown>{markdownContent.model_characteristics}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* How to Use Section */}
                {markdownContent.how_to_use && (
                  <section className="detail-section" id="how-to-use">
                    <h3>How to Use It</h3>
                    <div className="detail-content documentation-content">
                      <DocMarkdown>{markdownContent.how_to_use}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* Additional Resources Section */}
                {additionalResourceLinks.length > 0 && (
                  <section className="detail-section" id="additional-resources">
                    <h3>Additional Resources</h3>
                    <div className="additional-resources-list">
                      {additionalResources.filter(r => r.url).map((resource, idx) => {
                        const external =
                          resource.url &&
                          (resource.url.startsWith('http://') ||
                            resource.url.startsWith('https://'))
                        return (
                          <a
                            key={idx}
                            href={resolvePublicHref(resource.url)}
                            target={external ? '_blank' : undefined}
                            rel={external ? 'noopener noreferrer' : undefined}
                            className="additional-resource-item"
                          >
                            <i className="fas fa-arrow-up-right-from-square"></i>
                            <span>{resource.name}</span>
                          </a>
                        )
                      })}
                    </div>
                  </section>
                )}

                {/* Region Section -- inline chips */}
                {project?.countries?.length > 0 && (
                  <section className="detail-section" id="region">
                    <h3>Region</h3>
                    <div className="region-chips">
                      {project.countries.map(c => <span className="region-chip" key={c}>{c}</span>)}
                    </div>
                  </section>
                )}

                {/* Organizations Involved Section -- dot-list format */}
                {organizations && (
                  <section className="detail-section" id="organizations">
                    <h3>Organizations Involved</h3>
                    {organizations.raw ? (
                      <div className="documentation-content">
                        <DocMarkdown>{organizations.raw}</DocMarkdown>
                      </div>
                    ) : (
                      <div className="org-list">
                        {organizations.powered && (
                          <div className="org-list-item">
                            <span className="org-dot org-dot-powered"></span>
                            <div>
                              <span className="org-list-label">Powered by</span>
                              <div className="org-list-content"><DocMarkdown>{organizations.powered}</DocMarkdown></div>
                            </div>
                          </div>
                        )}
                        {organizations.catalyzed && (
                          <div className="org-list-item">
                            <span className="org-dot org-dot-catalyzed"></span>
                            <div>
                              <span className="org-list-label">Catalyzed by</span>
                              <div className="org-list-content"><DocMarkdown>{organizations.catalyzed}</DocMarkdown></div>
                            </div>
                          </div>
                        )}
                        {organizations.financed && (
                          <div className="org-list-item">
                            <span className="org-dot org-dot-financed"></span>
                            <div>
                              <span className="org-list-label">Financed by</span>
                              <div className="org-list-content"><DocMarkdown>{organizations.financed}</DocMarkdown></div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </section>
                )}

                {/* E) Metadata grid at bottom */}
                {(project?.authors || project?.contact || licenseValue || sdgs.length > 0) && (
                  <div className="panel-metadata-grid">
                    {project?.authors && (
                      <div className="metadata-cell">
                        <span className="metadata-label">Author</span>
                        <span className="metadata-value">{project.authors}</span>
                      </div>
                    )}
                    {project?.contact && (
                      <div className="metadata-cell">
                        <span className="metadata-label">Contact</span>
                        <span className="metadata-value">{renderContact(project.contact)}</span>
                      </div>
                    )}
                    {licenseValue && (
                      <div className="metadata-cell">
                        <span className="metadata-label">License</span>
                        <span className="metadata-value">{renderLicense(licenseValue)}</span>
                      </div>
                    )}
                    {sdgs.length > 0 && (
                      <div className="metadata-cell">
                        <span className="metadata-label">SDG</span>
                        <span className="metadata-value">{sdgs.join(', ')}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}

export default DetailPanel
