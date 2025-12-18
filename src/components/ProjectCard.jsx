import { withBasePath } from '../utils/basePath'

const urlRegex = /https?:\/\/[^\s)]+/i
const firstUrl = (text = '') => {
  if (!text || typeof text !== 'string') return null
  const match = text.match(urlRegex)
  return match ? match[0] : null
}

const cleanLabel = (label = '') =>
  label
    .replace(/\([^)]*\)/g, ' ') // remove parenthetical parts
    .replace(/\s{2,}/g, ' ')
    .trim()

const parseContact = (contact = '') => {
  if (!contact) return { label: '', href: null }
  const emailMatch = contact.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)
  const urlMatch = contact.match(urlRegex)

  // Prefer name before comma/paren as label
  const beforeComma = contact.split(',')[0].trim()
  const beforeParen = contact.split('(')[0].trim()
  const baseLabel = cleanLabel(beforeComma || beforeParen || contact)

  if (emailMatch) {
    const email = emailMatch[0]
    const label = cleanLabel(baseLabel.replace(email, '').trim()) || baseLabel || email
    return { label, href: `mailto:${email}` }
  }

  if (urlMatch) {
    const url = urlMatch[0]
    const label = cleanLabel(baseLabel.replace(url, '').trim()) || baseLabel || url
    return { label, href: url }
  }

  return { label: cleanLabel(contact), href: null }
}

const licenseLabel = (license = '') => {
  if (!license) return ''
  const normalized = license.trim().toLowerCase()
  // If it's just a version number like "4.0", normalize to cc-by-4.0
  if (/^\d+(\.\d+)?$/.test(normalized)) {
    return `cc-by-${normalized}`
  }
  const url = firstUrl(license)
  if (url) {
    const label = license.replace(url, '').trim()
    if (label) return label.toLowerCase()
    try {
      const u = new URL(url)
      // Prefer the last path segment if present (e.g., cc-by-4.0)
      const segments = u.pathname.split('/').filter(Boolean)
      const last = segments.length ? decodeURIComponent(segments[segments.length - 1]) : ''
      if (last) return last.toLowerCase()
      const host = u.hostname.replace(/^www\./, '')
      if (host) return host.toLowerCase()
    } catch {
      // ignore
    }
    try {
      const host = new URL(url).hostname.replace(/^www\./, '')
      return host ? host.toLowerCase() : 'license'
    } catch {
      return 'license'
    }
  }
  return normalized
}

const ProjectCard = ({ project, onClick }) => {
  const { title, description, sdgs, data_types, image, has_dataset, has_usecase, is_lacuna, is_on_hold, countries = [], contact, license } = project

  const cardClasses = [
    'card',
    has_dataset ? 'has-dataset' : '',
    has_usecase ? 'has-usecase' : '',
    is_lacuna ? 'has-lacuna' : ''
  ].filter(Boolean).join(' ')

  // Truncate description
  const maxLength = 200
  const truncatedDesc = description.length > maxLength 
    ? description.substring(0, maxLength) + '...'
    : description

  const imageUrl = image ? withBasePath(image) : null

  const countryLabel = countries.length > 0
    ? (countries.length > 2 ? `${countries.slice(0, 2).join(', ')} +${countries.length - 2}` : countries.join(', '))
    : null

  const truncateLabel = (text = '', max = 16) =>
    text.length > max ? `${text.slice(0, max)}…` : text

  const displayDataTypes = (() => {
    if (data_types.length > 2) {
      return [
        { label: truncateLabel(data_types[0]), full: data_types[0] },
        { label: truncateLabel(data_types[1]), full: data_types[1] },
        { label: `+${data_types.length - 2} more`, full: data_types.join(', '), isMore: true }
      ]
    }
    return data_types.map(dt => ({ label: truncateLabel(dt), full: dt }))
  })()

  const licenseValue = license && license.trim() ? license : 'cc-by-4.0'
  const licenseUrl = firstUrl(licenseValue)
  const licenseText = licenseLabel(licenseValue)

  const contactParsed = parseContact(contact)
  const showOnHoldNote = is_on_hold && !has_dataset && !has_usecase

  return (
    <div className={cardClasses} onClick={() => onClick(project)}>
      <div 
        className={`card-image${image ? ' has-image' : ''}`}
        style={imageUrl ? { backgroundImage: `url("${imageUrl}")` } : undefined}
      />
      
      <div className="card-header">
        {sdgs.length > 0 && (
          <div className="domain-badges">
            {sdgs.slice(0, 3).map(sdg => (
              <span key={sdg} className="domain-badge">
                {sdg}
              </span>
            ))}
          </div>
        )}
        <h3>{title}</h3>
      </div>
      
      <div className="card-body">
        <div className="card-meta-top">
          {countryLabel && (
            <div className="meta-item">
              <i className="fas fa-map-marker-alt"></i>
              <span>{countryLabel}</span>
            </div>
          )}
          {contactParsed.label && (
            <div className="meta-item">
              <i className="fas fa-user"></i>
              {contactParsed.href ? (
                <a
                  href={contactParsed.href}
                  target={contactParsed.href.startsWith('http') ? '_blank' : undefined}
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                >
                  {contactParsed.label}
                </a>
              ) : (
                <span>{contactParsed.label}</span>
              )}
            </div>
          )}
        </div>

          <div className="card-description">
          <div className="description-text collapsed">
            {truncatedDesc}
          </div>
          <div className="details-link">
            <i className="fas fa-arrow-right-long"></i>
            <span>Click card to see details</span>
          </div>
        </div>
      </div>
      
      <div className="card-footer">
        <div className="data-type-chips footer-chips">
          {displayDataTypes.map(dt => (
            <span
              key={dt.full || dt.label}
              className={`data-type-chip ${dt.isMore ? 'more-chip' : ''}`}
              data-filter={dt.full || dt.label}
              title={dt.full}
            >
              {dt.label}
            </span>
          ))}
        </div>
        {licenseValue && licenseText && (
          <div className="license-tag">
            <i className="fas fa-copyright"></i>
            {' '}
            {licenseUrl ? (
              <a href={licenseUrl} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                {licenseText || licenseUrl}
              </a>
            ) : (
              licenseText
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProjectCard

