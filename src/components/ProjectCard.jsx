import { withBasePath } from '../utils/basePath'
import { parseFirstSdg } from '../utils/sdgColors'
import { licenseLabel, firstUrl } from '../utils/parsing'
import { completenessFromScore, depthLabel } from '../utils/depth'
import { hasHealthSignal, availabilityLabel, contextLabel } from '../utils/health'
import RisoPrint from './RisoPrint'

const ProjectCard = ({ project, onClick, onFilterSDG, eager = false }) => {
  const {
    id, slug, title, description, sdgs = [], data_types = [], image,
    has_dataset, has_usecase, is_lacuna, has_access_note,
    countries = [], license, quality_score, health
  } = project

  // Real crawlable link to the project's prerendered page. Clicking opens the panel
  // in place (preventDefault); crawlers, middle-click and open-in-new-tab follow the href.
  const projectHref = withBasePath('projects/' + (slug || id) + '/')

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

  // No license recorded means unknown terms, not permissive ones -- asserting a
  // default here would state a reuse grant on the partner's behalf that nobody
  // verified. The card simply omits it; the detail panel says "Not specified".
  const licenseValue = license && license.trim() ? license : null
  const licenseUrl = licenseValue ? firstUrl(licenseValue) : null
  const licenseText = licenseValue ? licenseLabel(licenseValue) : ''

  const typeLabel = data_types.length > 0
    ? (data_types.length > 1 ? `${data_types[0]} +${data_types.length - 1}` : data_types[0])
    : null

  const primarySdg = parseFirstSdg(sdgs)

  return (
    <article className={cardClasses}>
      <div className="card-cover">
        <RisoPrint src={image ? withBasePath(image) : null} eager={eager} />
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

        <h3 className="card-title">
          <a
            href={projectHref}
            className="card-title-link"
            onClick={(e) => { e.preventDefault(); e.stopPropagation(); onClick(project) }}
          >
            {title}
          </a>
        </h3>
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
        {/* The SDG sits under the title rather than over the image: it is a way to
            filter, so it lives with the other small actions. The empty spans keep the
            license on the right when either side is missing (space-between). */}
        {primarySdg ? (
          <button
            className="card-sdg"
            onClick={(e) => { e.stopPropagation(); onFilterSDG?.(sdgs[0]) }}
            title={`Filter by ${primarySdg.label}`}
            type="button"
          >
            <span className="swatch" style={{ background: primarySdg.color || 'var(--press-ink)' }} aria-hidden="true"></span>
            <span className="card-sdg-text">
              {primarySdg.label}{primarySdg.name ? ` · ${primarySdg.name}` : ''}
            </span>
          </button>
        ) : (
          <span className="card-sdg" />
        )}
        {licenseText ? (
          <span className="card-license">
            {licenseUrl ? (
              <a href={licenseUrl} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                {licenseText}
              </a>
            ) : (
              licenseText
            )}
          </span>
        ) : (
          <span className="card-license" />
        )}
      </div>
    </article>
  )
}

export default ProjectCard
