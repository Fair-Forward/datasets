import { withBasePath } from '../utils/basePath'
import { SDG_COLORS } from '../utils/sdgColors'

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

const getSdgFallbackColor = (sdgs) => {
  if (!sdgs || sdgs.length === 0) return null
  const match = sdgs[0].match(/\d+/)
  return match ? SDG_COLORS[parseInt(match[0], 10)] : null
}

const ProjectCard = ({ project, onClick, onFilterSDG }) => {
  const { title, description, sdgs, data_types, image, has_dataset, has_usecase, is_lacuna, has_access_note, countries = [], license } = project

  const cardClasses = [
    'card',
    has_dataset ? 'has-dataset' : '',
    has_usecase ? 'has-usecase' : '',
    is_lacuna ? 'has-lacuna' : '',
    has_access_note ? 'has-access-note' : ''
  ].filter(Boolean).join(' ')

  // Truncate description
  const maxLength = 200
  const truncatedDesc = description.length > maxLength 
    ? description.substring(0, maxLength) + '...'
    : description

  const countryLabel = countries.length > 0
    ? (countries.length > 2 ? `${countries.slice(0, 2).join(', ')} +${countries.length - 2}` : countries.join(', '))
    : null

  const licenseValue = license && license.trim() ? license : 'cc-by-4.0'
  const licenseUrl = firstUrl(licenseValue)
  const licenseText = licenseLabel(licenseValue)

  const fallbackColor = !image ? getSdgFallbackColor(sdgs) : null

  return (
    <div
      className={cardClasses}
      onClick={() => onClick(project)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(project) } }}
      aria-label={`View details for ${title}`}
    >
      <div
        className={`card-image${image ? ' has-image' : ''}`}
        style={
          image
            ? { backgroundImage: `url("${withBasePath(image)}")` }
            : fallbackColor
              ? { backgroundImage: `linear-gradient(135deg, ${fallbackColor}20 0%, ${fallbackColor}44 100%)` }
              : undefined
        }
      />

      <div className="card-header">
        <h3>{title}</h3>
        {sdgs.length > 0 && (
          <div className="domain-badges">
            {sdgs.slice(0, 3).map(sdg => (
              <button
                key={sdg}
                className="domain-badge"
                onClick={(e) => { e.stopPropagation(); onFilterSDG?.(sdg); }}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation() } }}
                title={`Filter by ${sdg}`}
                type="button"
              >
                {sdg}
              </button>
            ))}
            {has_access_note && (
              <span className="access-note-chip" title="No public dataset/use-case link">
                <i className="fas fa-circle-info"></i> Info
              </span>
            )}
          </div>
        )}
      </div>
      
      <div className="card-body">
        <div className="card-meta-top">
          {countryLabel && (
            <div className="meta-item">
              <i className="fas fa-map-marker-alt"></i>
              <span>{countryLabel}</span>
            </div>
          )}
        </div>

          <div className="card-description">
          <div className="description-text collapsed">
            {truncatedDesc}
          </div>
        </div>
      </div>
      
      <div className="card-footer">
        {data_types.length > 0 && (
          <span className="footer-data-types">{data_types.join(', ')}</span>
        )}
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

