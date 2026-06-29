import { useState, useEffect, useCallback, useRef, Fragment } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { withBasePath, resolvePublicHref } from '../utils/basePath'
import { parseSdgList } from '../utils/sdgColors'
import { completenessFromScore, depthLabel } from '../utils/depth'
import { parseContacts, licenseLabel, firstUrl } from '../utils/parsing'
import { hasHealthSignal, availabilityLabel, contextLabel, healthDetailLines } from '../utils/health'
import { SITE_NAME } from '../utils/site'

// Cumulative maturity pipeline rendered as a stepper in the detail panel.
const MATURITY_STEPS = [
  { key: 'dataset', label: 'Dataset' },
  { key: 'model', label: 'Model' },
  { key: 'pilot', label: 'Pilot' },
  { key: 'usecase', label: 'Use case' },
  { key: 'business', label: 'Business' }
]

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
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownLinkComponents}>{children}</ReactMarkdown>
)

// Build shareable URL for a project using its stable slug
const getShareUrl = (slug) => {
  const url = new URL(window.location.href)
  url.searchParams.set('project', slug)
  return url.toString()
}

// Convert org text with inline URLs into proper markdown links
// "Org Name (https://url.com/)" -> "[Org Name](https://url.com/)"
// "(logo https://...)" -> stripped
// "OrgA, OrgB (url)" -> "OrgA, [OrgB](url)" (links only the closest org)
const linkifyOrgText = (text) => {
  if (!text) return text
  // Strip logo/image URLs: (logo https://...) or URLs ending in image extensions
  let result = text.replace(/\(logo\s+https?:\/\/[^\s)]+\)/gi, '')
  result = result.replace(/\(\s*https?:\/\/[^\s)]+\.(?:jpg|jpeg|png|gif|svg)\s*\)/gi, '')
  // Convert "Name (https://url)" - link only the org closest to the URL
  result = result.replace(/([^(\n]*?)\s*\(\s*(https?:\/\/[^\s)]+)\s*\)/g, (_match, name, url) => {
    const trimmed = name.trimStart()
    // Find split point after the last separator (comma, &, ;, " and ")
    let splitAfter = -1
    const commaIdx = trimmed.lastIndexOf(',')
    if (commaIdx >= 0) splitAfter = Math.max(splitAfter, commaIdx + 1)
    const ampIdx = trimmed.lastIndexOf('&')
    if (ampIdx >= 0) splitAfter = Math.max(splitAfter, ampIdx + 1)
    const semiIdx = trimmed.lastIndexOf(';')
    if (semiIdx >= 0) splitAfter = Math.max(splitAfter, semiIdx + 1)
    const andIdx = trimmed.lastIndexOf(' and ')
    if (andIdx >= 0) splitAfter = Math.max(splitAfter, andIdx + 5)
    if (splitAfter >= 0) {
      const prefix = trimmed.substring(0, splitAfter)
      const orgName = trimmed.substring(splitAfter).trim()
      return `${prefix} [${orgName}](${url})`
    }
    // Handle leading connectors like "and "
    const final = trimmed.trim()
    const connector = final.match(/^(and\s+)(.+)/i)
    if (connector) return `${connector[1]}[${connector[2].trim()}](${url})`
    return `[${final}](${url})`
  })
  // Convert "Name https://url" (bare URL after name, at end of segment)
  result = result.replace(/([^,&;\n[\]()]+?)\s+(https?:\/\/[^\s,&;)]+)(?=[,&;\n]|$)/g, (_match, name, url) => {
    return `[${name.trim()}](${url})`
  })
  return result.trim()
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
      remaining.search(/Powered by\s*(?:\/\s*Provided by)?:/i)
    ].filter(i => i >= 0)

    const endIdx = nextLabels.length > 0 ? Math.min(...nextLabels) : remaining.length
    return linkifyOrgText(remaining.substring(0, endIdx))
  }

  const powered = extractSection('Powered by\\s*(?:\\/\\s*Provided by)?')
  const catalyzed = extractSection('Catalyzed by')
  const financed = extractSection('Financed by')

  if (!powered && !catalyzed && !financed) {
    return { raw: linkifyOrgText(orgText) }
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
    project?.access_note_kind === 'documents'
      ? 'fa-folder-open'
      : 'fa-circle-info'
  const sdgs = project?.sdgs || []
  const dataTypes = project?.data_types || []
  const sdgList = parseSdgList(sdgs)
  const organizations = parseOrganizations(project?.organizations)
  const health = project?.health
  const showHealth = hasHealthSignal(health)
  const healthContext = showHealth ? contextLabel(health.context) : null
  const healthDetails = showHealth ? healthDetailLines(health) : []
  const brokenLinkCount = showHealth ? (health.broken_links?.length || 0) : 0

  // Compute license value for metadata grid
  const rawLicense = project?.license?.trim()
  const licenseValue = rawLicense || null

  const handleShare = useCallback(async () => {
    const url = getShareUrl(project.slug || project.id)
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      window.prompt('Copy this link:', url)
    }
  }, [project?.slug, project?.id])

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

        // Fetch the doc files in parallel so the panel opens without waiting on a
        // chain of sequential round-trips.
        await Promise.all(
          Object.entries(files).map(async ([key, filename]) => {
            try {
              const response = await fetch(withBasePath(`projects/${project.id}/docs/${filename}`))
              if (response.ok) {
                content[key] = await response.text()
              }
            } catch (err) {
              console.log(`Could not load ${filename}:`, err)
            }
          })
        )

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

  // Reflect the open project in the document title and social-preview tags so the
  // browser tab, bookmarks and screen readers show the project (not the generic
  // site title). Restored on close/unmount and when switching projects.
  useEffect(() => {
    if (!project) return
    const setMeta = (selector, value) => {
      const el = document.querySelector(selector)
      if (el) el.setAttribute('content', value)
    }
    const previousTitle = document.title
    const previousOgTitle = document.querySelector('meta[property="og:title"]')?.getAttribute('content')
    const previousTwTitle = document.querySelector('meta[name="twitter:title"]')?.getAttribute('content')

    const heading = `${project.title} - ${SITE_NAME}`
    document.title = heading
    setMeta('meta[property="og:title"]', heading)
    setMeta('meta[name="twitter:title"]', heading)

    return () => {
      document.title = previousTitle
      if (previousOgTitle != null) setMeta('meta[property="og:title"]', previousOgTitle)
      if (previousTwTitle != null) setMeta('meta[name="twitter:title"]', previousTwTitle)
    }
  }, [project])

  if (!project) return null

  const hasAnyLinks = datasetLinks.length > 0 || usecaseLinks.length > 0

  const additionalResourceLinks = additionalResources.filter(r => r.url)

  // A contact cell may list several people (separated by ';', ',' or '&'); parse
  // it into individual contacts so each name links to its own email, joined by '; '.
  const contacts = parseContacts(project?.contact || '')
  const renderContacts = () =>
    contacts.map(({ label, href }, i) => (
      <Fragment key={`${label}-${i}`}>
        {i > 0 && '; '}
        {href
          ? (href.startsWith('mailto:')
              ? <a href={href}>{label}</a>
              : <a href={href} target="_blank" rel="noopener noreferrer">{label}</a>)
          : label}
      </Fragment>
    ))

  // Render license value as JSX using shared parsing
  const renderLicense = (raw) => {
    const url = firstUrl(raw)
    const label = licenseLabel(raw)
    if (url) {
      return <a href={url} target="_blank" rel="noopener noreferrer">{label}</a>
    }
    return label
  }

  // --- Detail panel v2 derived values ---
  const sdgPrimary = sdgList[0] || null
  const eyebrowParts = []
  if (project?.countries?.length) eyebrowParts.push(project.countries[0])

  const qualityScore = project?.quality_score || 0
  const depthText = depthLabel(qualityScore)
  const depthDots = completenessFromScore(qualityScore)
  const dataTypeText = dataTypes.length ? dataTypes.join(', ') : null
  const maturityTags = project?.maturity_tags || []

  // Link-health status for the meta strip -- only assert health we actually have.
  let statusText = 'Not checked'
  let statusState = 'unknown'
  if (showHealth) {
    if (health.availability === 'available') {
      statusText = 'Links healthy'
      statusState = 'available'
    } else {
      statusText = 'Links may be down'
      statusState = 'unavailable'
    }
  }

  return (
    <>
      <div className="panel-overlay active" onClick={onClose}></div>
      <div className="detail-panel open" ref={panelRef} role="dialog" aria-modal="true" aria-label={project.title}>
        <div className="detail-panel-header">
          <button className="panel-back-btn" onClick={onClose}>
            <i className="fas fa-arrow-left" aria-hidden="true"></i> Back to catalogue
          </button>
          <div className="detail-panel-header-actions">
            <button
              className="panel-share-btn"
              onClick={handleShare}
              title={copied ? 'Link copied!' : 'Copy link to share'}
            >
              <i className={`fas ${copied ? 'fa-check' : 'fa-arrow-up-from-bracket'}`} aria-hidden="true"></i>
              {copied ? 'Copied!' : 'Share'}
            </button>
            <button className="close-panel-btn" onClick={onClose} aria-label="Close panel">
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>

        <div className="detail-panel-content">
          {loading ? (
            <div className="panel-loader">
              <div className="loader-spinner"></div>
              <p>Loading details...</p>
            </div>
          ) : (
            <>
              {/* Hero image -- leads the panel so the access button below reads as the main action */}
              {(() => {
                if (project.image) {
                  return (
                    <div
                      className="panel-header-image"
                      style={{ backgroundImage: `url("${withBasePath(project.image)}")` }}
                    />
                  )
                }
                const sdgColor = sdgPrimary?.color || null
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

              {/* Eyebrow + title + lede */}
              {eyebrowParts.length > 0 && (
                <div className="panel-eyebrow">
                  {eyebrowParts.join(' · ')}
                </div>
              )}
              {sdgList.length > 0 && (
                <div className="panel-sdg-chips">
                  {sdgList.map((s) => (
                    <span className="panel-sdg-chip" key={s.num}>
                      <span className="panel-sdg-chip-dot" style={{ background: s.color || 'var(--accent-teal)' }} />
                      {s.label}{s.name ? ` · ${s.name}` : ''}
                    </span>
                  ))}
                </div>
              )}
              <h1 className="panel-title">{project.title}</h1>
              {project?.description && (
                <div className="panel-lede">
                  <DocMarkdown>{project.description}</DocMarkdown>
                </div>
              )}

              {contacts.length > 0 && (
                <div className="panel-contact-callout">
                  <span className="panel-contact-label">Contact / Authors</span>
                  <span className="panel-contact-value">{renderContacts()}</span>
                </div>
              )}

              {/* Primary actions */}
              <div className="panel-actions">
                {hasAnyLinks ? (
                  <>
                    {datasetLinks.map((link, idx) => {
                      const external = link.url && (link.url.startsWith('http://') || link.url.startsWith('https://'))
                      const hasCustomName = link.name && link.name !== 'Link'
                      const genericLabel = idx === 0 ? 'Access Dataset' : `Access Dataset ${idx + 1}`
                      const label = hasCustomName ? link.name : genericLabel
                      return (
                        <a
                          key={`dataset-${idx}`}
                          className="panel-cta"
                          href={resolvePublicHref(link.url)}
                          target={external ? '_blank' : undefined}
                          rel={external ? 'noopener noreferrer' : undefined}
                        >
                          <i className="fas fa-database"></i>
                          {label}
                        </a>
                      )
                    })}
                    {usecaseLinks.map((link, idx) => {
                      const external = link.url && (link.url.startsWith('http://') || link.url.startsWith('https://'))
                      const hasCustomName = link.name && link.name !== 'Link'
                      const genericLabel = idx === 0 ? 'Access Model/System' : `Access Model/System ${idx + 1}`
                      const label = hasCustomName ? link.name : genericLabel
                      return (
                        <a
                          key={`usecase-${idx}`}
                          className="panel-cta"
                          href={resolvePublicHref(link.url)}
                          target={external ? '_blank' : undefined}
                          rel={external ? 'noopener noreferrer' : undefined}
                        >
                          <i className="fas fa-robot"></i>
                          {label}
                        </a>
                      )
                    })}
                  </>
                ) : showHostedDocuments ? (
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
                    className={`panel-access-note panel-access-note-${project.access_note_kind || 'info'}`}
                  >
                    <i className={`fas ${accessNoteIconClass}`}></i>
                    <div className="panel-access-note-body documentation-content">
                      <DocMarkdown>{project.access_note_markdown}</DocMarkdown>
                    </div>
                  </div>
                ) : null}
              </div>

              {/* Access note context (shown below documents CTA) */}
              {showHostedDocuments && showAccessCallout && (
                <div className={`panel-access-note panel-access-note-${project.access_note_kind || 'info'}`}>
                  <i className={`fas ${accessNoteIconClass}`}></i>
                  <div className="panel-access-note-body documentation-content">
                    <DocMarkdown>{project.access_note_markdown}</DocMarkdown>
                  </div>
                </div>
              )}

              {/* Meta strip: Data type | License | Documentation | Status */}
              <div className="panel-meta-strip">
                <div className="panel-meta-cell">
                  <div className="panel-meta-label">Data type</div>
                  <div className="panel-meta-value">{dataTypeText || '—'}</div>
                </div>
                <div className="panel-meta-cell">
                  <div className="panel-meta-label">License</div>
                  <div className="panel-meta-value">{licenseValue ? renderLicense(licenseValue) : 'Not specified'}</div>
                </div>
                <div className="panel-meta-cell">
                  <div className="panel-meta-label">Documentation</div>
                  <div className="panel-meta-value panel-meta-depth">
                    {depthText}
                    <span className="completeness-indicator" aria-hidden="true">
                      {[1, 2, 3, 4, 5].map(i => (
                        <span key={i} className={`completeness-dot${i <= depthDots ? ' filled' : ''}`} />
                      ))}
                    </span>
                  </div>
                </div>
                <div className="panel-meta-cell">
                  <div className="panel-meta-label">Status</div>
                  <div className={`panel-meta-value panel-status-value status-${statusState}`}>
                    <span className="status-dot" aria-hidden="true"></span>{statusText}
                  </div>
                </div>
              </div>

              {/* Link health -- availability, when it was last checked, and what was found */}
              {showHealth && (
                <div className={`panel-status health-${health.availability}`}>
                  <span className="health-dot" aria-hidden="true"></span>
                  <div className="panel-status-body">
                    <span className="panel-status-headline">
                      {availabilityLabel(health.availability)}
                      {healthContext && (
                        <span className="panel-status-context"> · {healthContext}</span>
                      )}
                    </span>
                    {healthDetails.length > 0 && (
                      <span className="panel-status-detail">{healthDetails.join(' · ')}</span>
                    )}
                    {brokenLinkCount > 0 && (
                      <span className="panel-status-broken">
                        {brokenLinkCount === 1
                          ? '1 link did not respond at the last check'
                          : `${brokenLinkCount} links did not respond at the last check`}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Maturity stepper */}
              {maturityTags.length > 0 && (
                <div className="panel-maturity">
                  <div className="panel-section-eyebrow">Maturity</div>
                  <div className="maturity-stepper">
                    {MATURITY_STEPS.map((step, i) => {
                      const reached = maturityTags.includes(step.key)
                      const prevReached = i > 0 && maturityTags.includes(MATURITY_STEPS[i - 1].key)
                      return (
                        <Fragment key={step.key}>
                          {i > 0 && <span className={`maturity-line${prevReached && reached ? ' filled' : ''}`}></span>}
                          <div className={`maturity-node${reached ? ' reached' : ''}`}>
                            <span className="maturity-dot"></span>
                            <span className="maturity-label">{step.label}</span>
                          </div>
                        </Fragment>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* D) Flat content sections */}
              <div className="panel-data active">
                {/* About -- only when the markdown adds detail beyond the lede shown up top */}
                {markdownContent.description &&
                  markdownContent.description.trim() !== (project?.description || '').trim() && (
                  <section className="detail-section" id="description">
                    <h3>About</h3>
                    <div className="detail-content documentation-content">
                      <DocMarkdown>{markdownContent.description}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* Data Characteristics -- data types already live in the meta strip above */}
                {markdownContent.data_characteristics?.trim() && (
                  <section className="detail-section" id="data-characteristics">
                    <h3>Data Characteristics</h3>
                    <div className="detail-content documentation-content">
                      <DocMarkdown>{markdownContent.data_characteristics}</DocMarkdown>
                    </div>
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
                              <span className="org-list-label">Powered by / Provided by</span>
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

                {/* Footer meta: Editor */}
                {project?.editor && (
                  <div className="panel-metadata-grid">
                    <div className="metadata-cell">
                      <span className="metadata-label">Editor of this information</span>
                      <span className="metadata-value">{project.editor}</span>
                    </div>
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
