// Maturity as the Insights chart prints it: one column per stage, cumulative like
// the catalogue's maturity filter ("Models+" = reached at least a model), and every
// column holding all projects, inked where the project reached the stage.
export const MATURITY_STAGES = [
  { key: 'dataset', label: 'Datasets', name: 'Dataset' },
  { key: 'model', label: 'Models+', name: 'Model' },
  { key: 'pilot', label: 'Pilots+', name: 'Pilot' },
  { key: 'usecase', label: 'Use cases+', name: 'Use case' },
  { key: 'business', label: 'Business model', name: 'Business model' }
]

const stageIndex = key => MATURITY_STAGES.findIndex(stage => stage.key === key)

// The last stage in pipeline order among a project's tags; null when untagged.
export const furthestStage = (project) => {
  const tags = project?.maturity_tags || []
  for (let i = MATURITY_STAGES.length - 1; i >= 0; i -= 1) {
    if (tags.includes(MATURITY_STAGES[i].key)) return MATURITY_STAGES[i].key
  }
  return null
}

const byTitle = (a, b) => (a.title || '').localeCompare(b.title || '', 'en')

// One order shared by every column, so a project keeps its place across them:
// furthest stage first, which makes each column's reached projects fill it from
// the bottom; with lacunaFirst, Lacuna Fund projects lead within a stage; then by
// title. Projects without a maturity stage have no place in the chart.
export const printOrder = (projects = [], { lacunaFirst = false } = {}) =>
  projects
    .filter(project => furthestStage(project))
    .sort((a, b) =>
      stageIndex(furthestStage(b)) - stageIndex(furthestStage(a)) ||
      (lacunaFirst ? Number(Boolean(b.is_lacuna)) - Number(Boolean(a.is_lacuna)) : 0) ||
      byTitle(a, b))

// Projects that reached at least this stage: what its catalogue filter returns.
export const reachedCount = (projects = [], key) =>
  projects.filter(project => project.maturity_tags?.includes(key)).length

// Where the i-th dot of a column sits: rows fill from the bottom, left to right.
export const gridSlot = (index, perRow) => ({ row: Math.floor(index / perRow), col: index % perRow })
