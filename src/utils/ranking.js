// Combined ranking score used to ORDER catalog cards (CatalogPage sort).
//
// It blends documentation completeness (quality_score, computed in the Python build and shown as
// the 5-dot "information depth" indicator) with the weekly health signal:
//   - a bounded activity boost where GitHub/Hugging Face expose recency/popularity, and
//   - an availability penalty when no in-scope link resolved at the last check.
//
// The 5 dots still reflect quality_score alone -- this only changes sort order. Entries with no
// activity signal get no boost and no penalty, so the catalog is not biased toward GitHub/HF hosts.
// Methodology: docs/health-thresholds.md.

// Max boost a maximally active project earns, in quality-score points. ~30% of the 0-140 range.
export const ACTIVITY_WEIGHT = 40
// Demotion applied when health.availability is 'unavailable' (no link resolved at last check).
export const UNAVAILABLE_PENALTY = 20

export const rankScore = (project) => {
  let score = project.quality_score || 0
  const health = project.health
  if (health) {
    if (health.availability === 'unavailable') score -= UNAVAILABLE_PENALTY
    if (typeof health.activity_score === 'number') {
      score += (health.activity_score / 100) * ACTIVITY_WEIGHT
    }
  }
  return score
}
