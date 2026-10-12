import { useMemo } from 'react'
import { summariseBySdg, dotStates } from '../utils/healthInsights'
import { formatDay } from '../utils/health'
import { withBasePath } from '../utils/basePath'

// Three views of the same unnamed dots. Their tabs sit in the section header, as the other
// sections' do.
export const OSS_VIEWS = [
  { key: 'open', label: 'Open assets' },
  { key: 'changed', label: 'Changed in 12 months' },
  { key: 'several', label: 'More than one contributor' },
]

// What an inked, a ringed and a faint dot mean in each view.
const KEYS = {
  open: ['measured on GitHub, Hugging Face or Zenodo', 'open, not measured: another host, an organisation page or not readable',
    'no open repository or record'],
  changed: ['changed in the last 12 months', 'no change in the last 12 months', 'not measured, or an archive record'],
  several: ['more than one contributor', 'one contributor', 'not measured, or no readable commit history'],
}

const FACTS = { changed: 'changed in the last 12 months', several: 'with more than one contributor' }

const goalName = (row) => (row.key === 'all' ? 'All projects' : `${row.label} ${row.name || ''}`.trim())

const projectsOf = (n, noun = 'project') => `${n} ${noun}${n === 1 ? '' : 's'}`

// The row as one sentence for screen readers; the dots and the count are hidden from them.
const sentence = (row, view, minGroup) => {
  if (view === 'open') {
    return `${goalName(row)}: ${row.open} of ${projectsOf(row.projects)} with an open repository, model or record, ` +
      `${row.measured} measured.`
  }
  const fact = view === 'changed' ? row.changed : row.several
  if (!fact) return `${goalName(row)}: fewer than ${minGroup} projects to compare, so no figures are shown.`
  return `${goalName(row)}: ${fact.yes} of ${projectsOf(fact.of, 'measured project')} ${FACTS[view]}.`
}

const countText = (row, view) => {
  if (view === 'open') return `${row.open} of ${row.projects}`
  const fact = view === 'changed' ? row.changed : row.several
  return fact ? `${fact.yes} of ${fact.of}` : null
}

// "SDG 1, 3, 6 or 17"
const goalList = (numbers) =>
  numbers.length > 1 ? `SDG ${numbers.slice(0, -1).join(', ')} or ${numbers[numbers.length - 1]}` : `SDG ${numbers[0]}`

const Dots = ({ states }) => (
  <span className="oss-dots" aria-hidden="true">
    {Array.from({ length: states.inked }, (_, i) => <span key={`i${i}`} className="oss-dot is-inked" />)}
    {Array.from({ length: states.ringed }, (_, i) => <span key={`r${i}`} className="oss-dot is-ringed" />)}
    {Array.from({ length: states.faint }, (_, i) => <span key={`f${i}`} className="oss-dot is-faint" />)}
  </span>
)

// CHAOSS metrics by SDG: every project one unnamed dot, grouped by state, so goals are compared
// and projects never are (CHAOSS advises against comparing projects). A goal with fewer projects
// to compare than the minimum shows no share.
const ChaossBySdg = ({ projects, health, view = 'open' }) => {
  const summary = useMemo(() => summariseBySdg(projects, health), [projects, health])
  if (!summary) return null
  const [inked, ringed, faint] = KEYS[view]

  return (
    <div className="oss-sdg" data-view={view}>
      <p className="oss-sdg-meta">
        Measured {formatDay(summary.measuredAt)}, following CHAOSS metric definitions.{' '}
        <a href={withBasePath('chaoss/')}>How we apply the CHAOSS metrics</a>
      </p>

      <p className="maturity-key oss-sdg-key" aria-live="polite">
        <span className="maturity-key-item"><span className="oss-dot is-inked" aria-hidden="true" />{inked}</span>
        <span className="maturity-key-item"><span className="oss-dot is-ringed" aria-hidden="true" />{ringed}</span>
        <span className="maturity-key-item"><span className="oss-dot is-faint" aria-hidden="true" />{faint}</span>
      </p>

      <ul className="oss-sdg-rows">
        {[summary.all, ...summary.rows].map(row => {
          const states = dotStates(row, view)
          return (
            <li key={row.key} className={`oss-sdg-row${row.key === 'all' ? ' is-all' : ''}`}>
              <span className="sr-only">{sentence(row, view, summary.minGroup)}</span>
              <span className="oss-sdg-label" aria-hidden="true">
                {row.color && <span className="swatch" style={{ background: row.color }} />}
                <span className="oss-sdg-goal">{row.label}</span>
                {row.name && <span className="oss-sdg-name" title={row.name}>{row.name}</span>}
              </span>
              {states
                ? <Dots states={states} />
                : <span className="oss-sdg-suppressed" aria-hidden="true">fewer than {summary.minGroup} to compare</span>}
              <span className="oss-sdg-count" aria-hidden="true">{countText(row, view)}</span>
            </li>
          )
        })}
      </ul>

      <p className="oss-sdg-notes">
        {summary.absentSdgs.length > 0 && `No projects address ${goalList(summary.absentSdgs)}. `}
        Projects can address several goals and count under each.
      </p>
    </div>
  )
}

export default ChaossBySdg
