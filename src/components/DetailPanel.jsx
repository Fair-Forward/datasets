import { useState, useEffect, useCallback, useRef, Fragment } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { withBasePath, resolvePublicHref } from '../utils/basePath'
import { parseSdgList } from '../utils/sdgColors'
import { completenessFromScore, depthLabel } from '../utils/depth'
import { parseContacts, licenseLabel, firstUrl, labelFromUrl } from '../utils/parsing'
import { hasHealthSignal, availabilityLabel, contextLabel, healthDetailLines } from '../utils/health'
import { SITE_NAME, SITE_TITLE, SITE_DESCRIPTION, SITE_URL, SITE_OG_IMAGE } from '../utils/site'

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

// Reshape a free-text field for the panel: split inline "•" bullet runs into a
// real markdown list and shorten bare URLs to friendly link text, so a source
// cell dumped as one "• A • B • https://long/url" line renders as a scannable
// block instead of a wall. The URL is always preserved as the link target.
const formatFreeText = (md) => {
  if (!md || typeof md !== 'string') return md
  let text = md.trim()
  // Drop a stray pair of wrapping quotes some source cells carry.
  if (text.length > 1 && text.startsWith('"') && text.endsWith('"')) {
    text = text.slice(1, -1).trim()
  }
  // Inline bullet separators -> real list items.
  if (text.includes('•')) {
    const parts = text.split('•').map(s => s.trim()).filter(Boolean)
    const lines = []
    parts.forEach((part, i) => {
      if (i === 0 && !text.trimStart().startsWith('•')) {
        lines.push(part, '')      // lead-in sentence stays a paragraph
      } else {
        lines.push(`- ${part}`)
      }
    })
    text = lines.join('\n')
  }
  // Angle-bracket autolinks <https://...> -> shortened markdown links.
  text = text.replace(/<(https?:\/\/[^>\s]+)>/g, (_m, url) => {
    const clean = url.replace(/[.,;:]+$/, '')
    const label = labelFromUrl(clean) || clean
    return `[${label}](${clean})`
  })
  // Shorten remaining bare URLs (those not already inside a markdown link) to a label.
  text = text.replace(/(^|[^([<\]])(https?:\/\/[^\s)]+)/g, (_m, pre, url) => {
    const clean = url.replace(/[.,;:]+$/, '')
    const label = labelFromUrl(clean) || clean
    return `${pre}[${label}](${clean})`
  })
  return text
}

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
      if (el && value != null) el.setAttribute('content', value)
    }
    const ensureCanonical = () => {
      let el = document.querySelector('link[rel="canonical"]')
      if (!el) {
        el = document.createElement('link')
        el.setAttribute('rel', 'canonical')
        document.head.appendChild(el)
      }
      return el
    }

    const heading = `${project.title} - ${SITE_NAME}`
    const raw = (project.description || '').replace(/\s+/g, ' ').trim()
    // Keep this truncation in sync with meta_description() in scripts/generate_seo_pages.py
    // so the runtime and prerendered descriptions match.
    const description = raw.length > 160 ? raw.slice(0, 157).trimEnd() + '...' : raw
    const slug = project.slug || project.id
    // Absolute URL of the content-rich prerendered page for this project.
    const canonicalUrl = `${window.location.origin}${withBasePath('projects/' + slug + '/')}`
    const imageUrl = project.image ? `${window.location.origin}${withBasePath(project.image)}` : SITE_OG_IMAGE

    document.title = heading
    setMeta('meta[property="og:title"]', heading)
    setMeta('meta[name="twitter:title"]', heading)
    if (description) {
      setMeta('meta[name="description"]', description)
      setMeta('meta[property="og:description"]', description)
      setMeta('meta[name="twitter:description"]', description)
    }
    setMeta('meta[property="og:url"]', canonicalUrl)
    setMeta('meta[property="og:image"]', imageUrl)
    setMeta('meta[name="twitter:image"]', imageUrl)
    ensureCanonical().setAttribute('href', canonicalUrl)

    // Restore the generic site tags on close/unmount/switch. We restore to the known site
    // defaults (not values captured from the DOM) because entering via a prerendered
    // /projects/<slug>/ page means the DOM already holds project-specific tags -- a
    // capture-and-restore would leave those stale on the catalog view.
    return () => {
      document.title = SITE_TITLE
      setMeta('meta[property="og:title"]', SITE_TITLE)
      setMeta('meta[name="twitter:title"]', SITE_TITLE)
      setMeta('meta[name="description"]', SITE_DESCRIPTION)
      setMeta('meta[property="og:description"]', SITE_DESCRIPTION)
      setMeta('meta[name="twitter:description"]', SITE_DESCRIPTION)
      setMeta('meta[property="og:url"]', SITE_URL)
      setMeta('meta[property="og:image"]', SITE_OG_IMAGE)
      setMeta('meta[name="twitter:image"]', SITE_OG_IMAGE)
      ensureCanonical().setAttribute('href', SITE_URL)
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
            <div className="panel-grid">
              {/* LEFT: narrative column -- header fields + free-text sections rendered as-is */}
              <div className="panel-narrative">
                {eyebrowParts.length > 0 && (
                  <div className="panel-eyebrow">{eyebrowParts.join(' · ')}</div>
                )}
                <h1 className="panel-title">{project.title}</h1>
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
                {contacts.length > 0 && (
                  <div className="panel-contact-top">
                    <div className="panel-contact-top-label">Contact / Authors</div>
                    <div className="panel-contact-top-value">{renderContacts()}</div>
                  </div>
                )}
                {project?.description && (
                  <div className="panel-lede">
                    <DocMarkdown>{project.description}</DocMarkdown>
                  </div>
                )}

                {/* About -- only when the markdown adds detail beyond the lede shown up top */}
                {markdownContent.description &&
                  markdownContent.description.trim() !== (project?.description || '').trim() && (
                  <section className="panel-freetext" id="description">
                    <div className="panel-freetext-label">About</div>
                    <div className="documentation-content">
                      <DocMarkdown>{markdownContent.description}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* Data Characteristics -- free-text, any shape */}
                {markdownContent.data_characteristics?.trim() && (
                  <section className="panel-freetext" id="data-characteristics">
                    <div className="panel-freetext-label">Data Characteristics</div>
                    <div className="documentation-content">
                      <DocMarkdown>{formatFreeText(markdownContent.data_characteristics)}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* Model / Use Case Characteristics -- free-text, only when present */}
                {markdownContent.model_characteristics?.trim() && (
                  <section className="panel-freetext" id="model-characteristics">
                    <div className="panel-freetext-label">Model / Use Case Characteristics</div>
                    <div className="documentation-content">
                      <DocMarkdown>{formatFreeText(markdownContent.model_characteristics)}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* How to Use It -- free-text */}
                {markdownContent.how_to_use && (
                  <section className="panel-freetext" id="how-to-use">
                    <div className="panel-freetext-label">How to Use It</div>
                    <div className="documentation-content">
                      <DocMarkdown>{formatFreeText(markdownContent.how_to_use)}</DocMarkdown>
                    </div>
                  </section>
                )}

                {/* Additional Resources -- only when present */}
                {additionalResourceLinks.length > 0 && (
                  <section className="panel-freetext" id="additional-resources">
                    <div className="panel-freetext-label">Additional Resources</div>
                    <div className="additional-resources-list">
                      {additionalResourceLinks.map((resource, idx) => {
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
              </div>

              {/* RIGHT: facts rail -- reliable catalogue fields + access */}
              <div className="panel-rail">
                {/* Cover image */}
                {(() => {
                  if (project.image) {
                    return (
                      <div
                        className="panel-rail-image"
                        style={{ backgroundImage: `url("${withBasePath(project.image)}")` }}
                      />
                    )
                  }
                  const sdgColor = sdgPrimary?.color || null
                  if (sdgColor) {
                    return (
                      <div
                        className="panel-rail-image no-image"
                        style={{ backgroundImage: `linear-gradient(135deg, ${sdgColor}18 0%, ${sdgColor}35 100%)` }}
                      />
                    )
                  }
                  return null
                })()}

                {/* Datasets / Models access clusters (or documents / access-note fallback) */}
                {hasAnyLinks ? (
                  <>
                    {datasetLinks.length > 0 && (
                      <div className="rail-cluster">
                        <div className="rail-cluster-label">Datasets</div>
                        <div className="rail-chips-col">
                          {datasetLinks.map((link, idx) => {
                            const external = link.url && (link.url.startsWith('http://') || link.url.startsWith('https://'))
                            const hasCustomName = link.name && link.name !== 'Link'
                            const fallback = idx === 0 ? 'Access dataset' : `Access dataset ${idx + 1}`
                            const label = hasCustomName ? link.name : (labelFromUrl(link.url) || fallback)
                            return (
                              <a
                                key={`dataset-${idx}`}
                                className="rail-chip"
                                href={resolvePublicHref(link.url)}
                                target={external ? '_blank' : undefined}
                                rel={external ? 'noopener noreferrer' : undefined}
                              >
                                <span>{label}</span>
                                <i className="fas fa-arrow-up-right-from-square" aria-hidden="true"></i>
                              </a>
                            )
                          })}
                        </div>
                      </div>
                    )}
                    {usecaseLinks.length > 0 && (
                      <div className="rail-cluster">
                        <div className="rail-cluster-label">Models &amp; systems</div>
                        <div className="rail-chips-col">
                          {usecaseLinks.map((link, idx) => {
                            const external = link.url && (link.url.startsWith('http://') || link.url.startsWith('https://'))
                            const hasCustomName = link.name && link.name !== 'Link'
                            const fallback = idx === 0 ? 'Access model/system' : `Access model/system ${idx + 1}`
                            const label = hasCustomName ? link.name : (labelFromUrl(link.url) || fallback)
                            return (
                              <a
                                key={`usecase-${idx}`}
                                className="rail-chip"
                                href={resolvePublicHref(link.url)}
                                target={external ? '_blank' : undefined}
                                rel={external ? 'noopener noreferrer' : undefined}
                              >
                                <span>{label}</span>
                                <i className="fas fa-arrow-up-right-from-square" aria-hidden="true"></i>
                              </a>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </>
                ) : showHostedDocuments ? (
                  <div className="rail-cluster">
                    <div className="rail-cluster-label">Documents</div>
                    <div className="rail-chips-col">
                      {hostedDocuments.map((doc, idx) => {
                        const isPdf = doc.url?.toLowerCase().endsWith('.pdf')
                        return (
                          <a
                            key={`hosted-${idx}`}
                            className="rail-doc-link"
                            href={resolvePublicHref(doc.url)}
                          >
                            <i className={`fas ${isPdf ? 'fa-file-pdf' : 'fa-file-arrow-down'}`} aria-hidden="true"></i>
                            <span>{doc.name || 'Download Document'}</span>
                          </a>
                        )
                      })}
                    </div>
                  </div>
                ) : null}

                {/* Access note (shown when there is no public dataset/use-case link) */}
                {showAccessCallout && (
                  <div className={`rail-access-note rail-access-note-${project.access_note_kind || 'info'}`}>
                    <div className="rail-access-note-label">
                      <i className={`fas ${accessNoteIconClass}`} aria-hidden="true"></i> Access note
                    </div>
                    <div className="rail-access-note-body documentation-content">
                      <DocMarkdown>{project.access_note_markdown}</DocMarkdown>
                    </div>
                  </div>
                )}

                {/* Facts */}
                <div className="rail-facts">
                  <div className="rail-fact-row">
                    <span className="rail-fact-label">Data type</span>
                    <span className="rail-fact-value">{dataTypeText || '—'}</span>
                  </div>
                  <div className="rail-fact-row">
                    <span className="rail-fact-label">License</span>
                    <span className="rail-fact-value">
                      {licenseValue ? renderLicense(licenseValue) : <span className="rail-fact-empty">Not specified</span>}
                    </span>
                  </div>
                  <div className="rail-fact-row">
                    <span className="rail-fact-label">Documentation</span>
                    <span className="rail-fact-value rail-fact-depth">
                      {depthText}
                      <span className="completeness-indicator" aria-hidden="true">
                        {[1, 2, 3, 4, 5].map(i => (
                          <span key={i} className={`completeness-dot${i <= depthDots ? ' filled' : ''}`} />
                        ))}
                      </span>
                    </span>
                  </div>
                  <div className="rail-fact-row">
                    <span className="rail-fact-label">Status</span>
                    <span className={`rail-fact-value rail-status status-${statusState}`}>
                      <span className="status-dot" aria-hidden="true"></span>{statusText}
                    </span>
                  </div>
                  {project?.countries?.length > 0 && (
                    <div className="rail-fact-row">
                      <span className="rail-fact-label">Country</span>
                      <span className="rail-fact-value">{project.countries.join(', ')}</span>
                    </div>
                  )}
                </div>

                {/* Link health -- kept whenever there is more to report than the Status row */}
                {showHealth && (healthDetails.length > 0 || brokenLinkCount > 0 || healthContext) && (
                  <div className={`rail-health health-${health.availability}`}>
                    <span className="health-dot" aria-hidden="true"></span>
                    <div className="rail-health-body">
                      <span className="rail-health-headline">
                        {availabilityLabel(health.availability)}
                        {healthContext && (
                          <span className="rail-health-context"> · {healthContext}</span>
                        )}
                      </span>
                      {healthDetails.length > 0 && (
                        <span className="rail-health-detail">{healthDetails.join(' · ')}</span>
                      )}
                      {brokenLinkCount > 0 && (
                        <span className="rail-health-broken">
                          {brokenLinkCount === 1
                            ? '1 link did not respond at the last check'
                            : `${brokenLinkCount} links did not respond at the last check`}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Maturity -- vertical stepper */}
                {maturityTags.length > 0 && (
                  <div className="rail-maturity">
                    <div className="rail-cluster-label">Maturity</div>
                    <div className="rail-stepper">
                      {MATURITY_STEPS.map((step, i) => {
                        const reached = maturityTags.includes(step.key)
                        const prevReached = i > 0 && maturityTags.includes(MATURITY_STEPS[i - 1].key)
                        return (
                          <Fragment key={step.key}>
                            {i > 0 && (
                              <span className={`rail-step-line${prevReached && reached ? ' filled' : ''}`}></span>
                            )}
                            <div className={`rail-step${reached ? ' reached' : ''}`}>
                              <span className="rail-step-dot"></span>
                              <span className="rail-step-label">{step.label}</span>
                            </div>
                          </Fragment>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* Organisations + Contact + Editor */}
                {(organizations || project?.editor) && (
                  <div className="rail-orgs">
                    {organizations && (organizations.raw ? (
                      <div className="rail-org">
                        <div className="rail-org-label">Organizations Involved</div>
                        <div className="rail-org-value documentation-content"><DocMarkdown>{organizations.raw}</DocMarkdown></div>
                      </div>
                    ) : (
                      <>
                        {organizations.powered && (
                          <div className="rail-org">
                            <div className="rail-org-label"><span className="rail-org-dot" style={{ background: 'var(--primary)' }}></span> Powered by / Provided by</div>
                            <div className="rail-org-value documentation-content"><DocMarkdown>{organizations.powered}</DocMarkdown></div>
                          </div>
                        )}
                        {organizations.catalyzed && (
                          <div className="rail-org">
                            <div className="rail-org-label"><span className="rail-org-dot" style={{ background: 'var(--accent-gold)' }}></span> Catalyzed by</div>
                            <div className="rail-org-value documentation-content"><DocMarkdown>{organizations.catalyzed}</DocMarkdown></div>
                          </div>
                        )}
                        {organizations.financed && (
                          <div className="rail-org">
                            <div className="rail-org-label"><span className="rail-org-dot" style={{ background: 'var(--text-muted)' }}></span> Financed by</div>
                            <div className="rail-org-value documentation-content"><DocMarkdown>{organizations.financed}</DocMarkdown></div>
                          </div>
                        )}
                      </>
                    ))}

                    {project?.editor && (
                      <div className="rail-contact-block">
                        <div className="rail-org">
                          <div className="rail-org-label">Editor of this information</div>
                          <div className="rail-editor-value">{project.editor}</div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default DetailPanel
