import { withBasePath } from '../utils/basePath'
import { SDG_COLORS, SDG_NAMES } from '../utils/sdgColors'
import { licenseLabel, firstUrl } from '../utils/parsing'
import { completenessFromScore, depthLabel } from '../utils/depth'
import { hasHealthSignal, availabilityLabel, contextLabel } from '../utils/health'

const getSdgNumber = (sdgs) => {
  if (!sdgs || sdgs.length === 0) return null
  const match = sdgs[0].match(/\d+/)
  return match ? parseInt(match[0], 10) : null
}

const ProjectCard = ({ project, onClick, onFilterSDG }) => {
  const {
    title, description, sdgs = [], data_types = [], image,
    has_dataset, has_usecase, is_lacuna, has_access_note,
    countries = [], license, quality_score, health
  } = project

  const qs = quality_score || 0
  const completeness = completenessFromScore(qs)
  const depth = depthLabel(qs)

  // Surface link-health only when a link is unavailable -- flags dead links in the
  // grid (so they don't look identical to healthy ones) without adding a badge to
  // every healthy card.
  const showHealthWarning = hasHealthSignal(health) && health.availability === 'unavailable'
  const healthContext = showHealthWarning ? contextLabel(health.context) : null

  const cardClasses = [
    'card',
    has_dataset ? 'has-dataset' : '',
    has_usecase ? 'has-usecase' : '',
    is_lacuna ? 'has-lacuna' : '',
    has_access_note ? 'has-access-note' : ''
  ].filter(Boolean).join(' ')

  // Short description -- two lines on the card, full text in the detail panel.
  const maxLength = 160
  const truncatedDesc = description && description.length > maxLength
    ? description.substring(0, maxLength).trimEnd() + '…'
    : description

  const countryLabel = countries.length > 0
    ? (countries.length > 2 ? `${countries.slice(0, 2).join(', ')} +${countries.length - 2}` : countries.join(', '))
    : null

  const licenseValue = license && license.trim() ? license : 'CC-BY 4.0'
  const licenseUrl = firstUrl(licenseValue)
  const licenseText = licenseLabel(licenseValue)

  const typeLabel = data_types.length > 0
    ? (data_types.length > 1 ? `${data_types[0]} +${data_types.length - 1}` : data_types[0])
    : null

  const sdgNum = getSdgNumber(sdgs)
  const sdgColor = sdgNum ? SDG_COLORS[sdgNum] : null
  const sdgName = sdgNum ? SDG_NAMES[sdgNum] : null
  const fallbackColor = !image ? sdgColor : null

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
      >
        {sdgNum && (
          <button
            className="card-sdg-badge"
            onClick={(e) => { e.stopPropagation(); onFilterSDG?.(sdgs[0]) }}
            title={`Filter by ${sdgs[0]}`}
            type="button"
          >
            <span className="card-sdg-dot" style={{ background: sdgColor || 'var(--accent-teal)' }}></span>
            {sdgs[0]}{sdgName ? ` · ${sdgName}` : ''}
          </button>
        )}
      </div>

      <div className="card-body">
        <div className="card-meta-top">
          {countryLabel
            ? <span className="card-country">{countryLabel}</span>
            : <span className="card-country" />}
          <span className="card-depth" title={`Documentation depth: ${completeness}/5`}>
            <span className="completeness-indicator" aria-hidden="true">
              {[1, 2, 3, 4, 5].map(i => (
                <span key={i} className={`completeness-dot${i <= completeness ? ' filled' : ''}`} />
              ))}
            </span>
            <span className="depth-label">{depth}</span>
          </span>
        </div>

        <h3>{title}</h3>
        {truncatedDesc && <p className="card-desc">{truncatedDesc}</p>}

        {(typeLabel || has_access_note || showHealthWarning) && (
          <div className="card-tags">
            {typeLabel && <span className="card-type-tag">{typeLabel}</span>}
            {has_access_note && (
              <span className="card-access-badge" title="No public dataset/use-case link">
                <i className="fas fa-circle-info" aria-hidden="true"></i> Info
              </span>
            )}
            {showHealthWarning && (
              <span className={`health-badge health-${health.availability}`} title="Link check">
                <span className="health-dot" aria-hidden="true"></span>
                <span>{availabilityLabel(health.availability)}{healthContext ? ` · ${healthContext}` : ''}</span>
              </span>
            )}
          </div>
        )}
      </div>

      <div className="card-footer">
        {licenseText && (
          <span className="card-license">
            {licenseUrl ? (
              <a href={licenseUrl} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                {licenseText}
              </a>
            ) : (
              licenseText
            )}
          </span>
        )}
        <span className="card-cta">
          View details <i className="fas fa-arrow-right" aria-hidden="true"></i>
        </span>
      </div>
    </div>
  )
}

export default ProjectCard
