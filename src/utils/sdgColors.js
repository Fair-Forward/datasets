// Official UN SDG colors
export const SDG_COLORS = {
  1: '#E5243B',   // No Poverty
  2: '#DDA63A',   // Zero Hunger
  3: '#4C9F38',   // Good Health
  4: '#C5192D',   // Quality Education
  5: '#FF3A21',   // Gender Equality
  6: '#26BDE2',   // Clean Water
  7: '#FCC30B',   // Affordable Energy
  8: '#A21942',   // Decent Work
  9: '#FD6925',   // Industry Innovation
  10: '#DD1367',  // Reduced Inequalities
  11: '#FD9D24',  // Sustainable Cities
  12: '#BF8B2E',  // Responsible Consumption
  13: '#3F7E44',  // Climate Action
  14: '#0A97D9',  // Life Below Water
  15: '#56C02B',  // Life on Land
  16: '#00689D',  // Peace Justice
  17: '#19486A'   // Partnerships
}

export const SDG_NAMES = {
  1: 'No Poverty',
  2: 'Zero Hunger',
  3: 'Good Health & Well-being',
  4: 'Quality Education',
  5: 'Gender Equality',
  6: 'Clean Water & Sanitation',
  7: 'Affordable & Clean Energy',
  8: 'Decent Work & Economic Growth',
  9: 'Industry, Innovation & Infrastructure',
  10: 'Reduced Inequalities',
  11: 'Sustainable Cities & Communities',
  12: 'Responsible Consumption & Production',
  13: 'Climate Action',
  14: 'Life Below Water',
  15: 'Life on Land',
  16: 'Peace, Justice & Strong Institutions',
  17: 'Partnerships for the Goals'
}

// Normalize a raw SDG list (e.g. ["SDG 15", "SDG 13"]) into structured entries,
// preserving first-seen order, deduped, valid numbers only (1-17). Used by both
// the catalog tile (first entry) and the detail panel (all entries) so the two
// always agree on which SDG is "first".
export const parseSdgList = (sdgs = []) => {
  const seen = new Set()
  const out = []
  for (const raw of sdgs) {
    const match = String(raw).match(/SDG\s*(\d+)/i)
    if (!match) continue
    const num = parseInt(match[1], 10)
    if (num < 1 || num > 17 || seen.has(num)) continue
    seen.add(num)
    out.push({ num, label: `SDG ${num}`, name: SDG_NAMES[num] || null, color: SDG_COLORS[num] || null })
  }
  return out
}

// Return only the first valid SDG entry without building the whole list. Used by
// the catalog tile, which renders many cards and needs just the primary SDG.
export const parseFirstSdg = (sdgs = []) => {
  for (const raw of sdgs || []) {
    const match = String(raw).match(/SDG\s*(\d+)/i)
    if (!match) continue
    const num = parseInt(match[1], 10)
    if (num < 1 || num > 17) continue
    return { num, label: `SDG ${num}`, name: SDG_NAMES[num] || null, color: SDG_COLORS[num] || null }
  }
  return null
}
