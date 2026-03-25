import { withBasePath } from '../utils/basePath'
import { SDG_COLORS } from '../utils/sdgColors'
import { parseContact, licenseLabel, firstUrl } from '../utils/parsing'

const getSdgFallbackColor = (sdgs) => {
  if (!sdgs || sdgs.length === 0) return null
  const match = sdgs[0].match(/\d+/)
  return match ? SDG_COLORS[parseInt(match[0], 10)] : null
}

const ProjectCard = ({ project, onClick, onFilterSDG }) => {
  const { title, description, sdgs, data_types, image, has_dataset, has_usecase, is_lacuna, has_access_note, countries = [], license, quality_score } = project
  const completeness = Math.min(5, Math.max(1, Math.ceil((quality_score || 0) / 20)))

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
        <div className="completeness-indicator" title={`Information depth: ${completeness}/5`}>
          {[1, 2, 3, 4, 5].map(i => (
            <span key={i} className={`completeness-dot${i <= completeness ? ' filled' : ''}`} />
          ))}
        </div>
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

