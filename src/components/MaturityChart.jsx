import { Fragment, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { MATURITY_STAGES, furthestStage, gridSlot, printOrder, reachedCount } from '../utils/maturity'

// Three views of the same dots. Their tabs sit in the section header, as the SDG
// section's do.
export const MATURITY_STEPS = [
  { key: 'reached', label: 'What projects reached' },
  { key: 'lacuna', label: 'Lacuna Fund projects' },
  { key: 'reuse', label: 'Reuse by others' }
]

// Dots per row on wide screens, tablets and phones; insights.css picks the layout.
const PER_ROW = [8, 6, 5]

const STAGE_PHRASES = {
  dataset: 'have a dataset',
  model: 'reached at least a model',
  pilot: 'reached at least a pilot',
  usecase: 'reached at least a use case',
  business: 'reached a business model'
}

const stageName = key => MATURITY_STAGES.find(stage => stage.key === key)?.name

// Every column holds every project, in the same place: inked where the project
// reached the stage within our programme, open (pale) where the work is there for
// others to take further. So no column loses projects; the ink shows what we
// followed up, the rest stays open. A project lights up across all five columns.
const MaturityChart = ({ projects, step = 'reached' }) => {
  const chartRef = useRef(null)
  const [tip, setTip] = useState(null)
  const [pointed, setPointed] = useState(null)

  const order = printOrder(projects, { lacunaFirst: step === 'lacuna' })
  if (order.length === 0) {
    return <div className="maturity-chart-empty">No maturity data available</div>
  }

  const lacuna = order.filter(project => project.is_lacuna).length
  const rows = Object.fromEntries(PER_ROW.map(n => [`--rows-${n}`, Math.ceil(order.length / n)]))
  const slots = order.map((_, i) => PER_ROW.reduce((vars, n) => {
    const { row, col } = gridSlot(i, n)
    return { ...vars, [`--r${n}`]: row, [`--c${n}`]: col }
  }, { '--i': i }))

  // The project's name, set just above the dot under the pointer.
  const showTip = (event, project, column) => {
    const chart = chartRef.current?.getBoundingClientRect()
    if (!chart) return
    const dot = event.currentTarget.getBoundingClientRect()
    setTip({
      project,
      x: dot.left + dot.width / 2 - chart.left,
      y: dot.top - chart.top,
      align: column === 0 ? 'start' : column === MATURITY_STAGES.length - 1 ? 'end' : 'center'
    })
  }

  return (
    <div className="maturity" data-step={step} style={rows}>
      <p className="maturity-key" aria-live="polite">
        {step === 'lacuna' ? (
          <span className="maturity-key-item">
            <span className="maturity-swatch is-reached" aria-hidden="true" />
            Lacuna Fund projects: {lacuna}
          </span>
        ) : (
          <>
            <span className="maturity-key-item">
              <span className="maturity-swatch is-reached" aria-hidden="true" />
              Reached within our projects
            </span>
            <span className="maturity-key-item">
              <span className="maturity-swatch is-open" aria-hidden="true" />
              {step === 'reuse' ? 'Open for anyone to build on' : 'Open for others to build on'}
            </span>
          </>
        )}
      </p>

      <div className="maturity-chart" ref={chartRef}>
        {MATURITY_STAGES.map((stage, column) => {
          const count = reachedCount(order, stage.key)
          return (
            <Fragment key={stage.key}>
              <div
                className={`maturity-column${column > 0 ? ' is-open-ended' : ''}${pointed === stage.key ? ' is-pointed' : ''}`}
                style={{ gridColumn: column + 1 }}
              >
                {order.map((project, i) => {
                  const reached = project.maturity_tags.includes(stage.key)
                  return (
                    <Link
                      key={project.id}
                      to={`/?project=${project.slug || project.id}`}
                      className={`maturity-dot ${reached ? 'is-reached' : 'is-open'}` +
                        (project.is_lacuna ? ' is-lacuna' : '') +
                        (tip?.project.id === project.id ? ' is-hovered' : '')}
                      style={slots[i]}
                      tabIndex={-1}
                      aria-hidden="true"
                      onMouseEnter={(e) => showTip(e, project, column)}
                      onMouseLeave={() => setTip(null)}
                    />
                  )
                })}
              </div>
              <Link
                to={`/?maturity=${stage.key}`}
                className="maturity-label"
                style={{ gridColumn: column + 1 }}
                aria-label={`${stage.label}: ${count} of ${order.length} projects ${STAGE_PHRASES[stage.key]}. Show them in the catalogue`}
                onMouseEnter={() => setPointed(stage.key)}
                onMouseLeave={() => setPointed(null)}
                onFocus={() => setPointed(stage.key)}
                onBlur={() => setPointed(null)}
              >
                <span className="maturity-count">{count}</span>
                <span className="maturity-stage">{stage.label}</span>
              </Link>
            </Fragment>
          )
        })}

        {tip && (
          <div className={`maturity-tip is-${tip.align}`} style={{ left: tip.x, top: tip.y }} aria-hidden="true">
            <span className="maturity-tip-title">{tip.project.title}</span>
            <span className="maturity-tip-meta">
              Reached: {stageName(furthestStage(tip.project))}
              {tip.project.is_lacuna ? ' · Lacuna Fund project' : ''}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

export default MaturityChart
