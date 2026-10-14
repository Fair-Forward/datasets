// The detail panel rail's "Online Community Health measured through CHAOSS metrics" block: facts about a project's open assets, measured
// weekly with the metrics of CHAOSS (Community Health Analytics in Open Source Software, a Linux
// Foundation project), in hairline rows like the facts above it. Each row label names the CHAOSS
// metric it follows on hover. Rows without enough data are named in one line instead of showing a
// zero. The block describes and never grades: no colours, no dots, no score. `block` comes from
// ossBlock() in utils/health.
const ChaossMetrics = ({ block, href }) => {
  const caption = `${block.dateLabel[0].toUpperCase()}${block.dateLabel.slice(1)} ${block.date}` +
    (block.scope ? ` ${block.scope}` : '')

  return (
    <div className="rail-oss">
      <div className="rail-cluster-label">Online Community Health measured through CHAOSS metrics</div>
      <p className="rail-oss-caption">{caption}</p>
      {block.note && <p className="rail-oss-caption">{block.note}</p>}

      <dl className="rail-oss-rows">
        {block.rows.map(row => (
          <div className="rail-oss-row" key={row.key}>
            <dt title={`CHAOSS metric: ${row.chaoss}`}>{row.label}</dt>
            <dd>{row.lines.map(line => <span key={line}>{line}</span>)}</dd>
          </div>
        ))}
        {block.gaps && (
          <div className="rail-oss-row is-gap">
            <dt>{block.gapsLabel}</dt>
            <dd><span>{block.gaps}</span></dd>
          </div>
        )}
      </dl>

      <a className="rail-oss-method" href={href}>
        How the CHAOSS metrics are measured
        <i className="fas fa-arrow-right" aria-hidden="true"></i>
      </a>
    </div>
  )
}

export default ChaossMetrics
