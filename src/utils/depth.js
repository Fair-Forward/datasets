// Documentation-depth helpers derived from a project's quality_score (0-100).
// The catalogue surfaces this as a 1-5 dot indicator plus a short label; keeping
// the mapping here means the project card and the detail panel always agree.

export const completenessFromScore = (score = 0) =>
  score >= 90 ? 5 : score >= 75 ? 4 : score >= 60 ? 3 : score >= 40 ? 2 : 1

export const depthLabel = (score = 0) =>
  score >= 90 ? 'In-depth'
    : score >= 75 ? 'Detailed'
      : score >= 60 ? 'Documented'
        : score >= 40 ? 'Overview'
          : 'Minimal'
