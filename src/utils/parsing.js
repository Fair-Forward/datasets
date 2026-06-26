const urlRegex = /https?:\/\/[^\s)]+/i

export const firstUrl = (text = '') => {
  if (!text || typeof text !== 'string') return null
  const match = text.match(urlRegex)
  return match ? match[0] : null
}

export const cleanLabel = (label = '') =>
  label
    .replace(/\([^)]*\)/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim()

const emailRegex = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i

// Drop angle-bracket wrappers (e.g. <email>) and trim stray separators left
// behind after an email/URL is removed from a label.
const stripContactPunctuation = (label = '') =>
  label
    .replace(/<[^>]*>/g, ' ')
    .replace(/[<>]/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .replace(/^[\s,;:&-]+|[\s,;:&-]+$/g, '')
    .trim()

// Parse a single contact segment into a display label and an optional link.
export const parseContact = (contact = '') => {
  if (!contact || typeof contact !== 'string') return { label: '', href: null }
  const emailMatch = contact.match(emailRegex)
  const urlMatch = contact.match(urlRegex)

  if (emailMatch) {
    const email = emailMatch[0]
    const label = stripContactPunctuation(cleanLabel(contact.replace(email, ' '))) || email
    return { label, href: `mailto:${email}` }
  }

  if (urlMatch) {
    const rawUrl = urlMatch[0]
    const url = rawUrl.replace(/[.,;:]+$/, '')
    const label = stripContactPunctuation(cleanLabel(contact.replace(rawUrl, ' '))) || url
    return { label, href: url }
  }

  return { label: stripContactPunctuation(cleanLabel(contact)), href: null }
}

// Split a raw contact cell into individual contacts, binding each email/URL to
// the name text that precedes it. Returns an array of { label, href }.
export const parseContacts = (raw = '') => {
  if (!raw || typeof raw !== 'string') return []

  // ';', newlines and runs of 3+ spaces always separate distinct contacts.
  const pieces = raw.split(/\s*;\s*|\n+|\s{3,}/)

  // ' & ' separates contacts only when it joins two email-bearing parts, so joint
  // organisation names like "Health & Welfare" are left intact.
  const groups = []
  for (const piece of pieces) {
    const ampParts = piece.split(/\s+&\s+/)
    if (ampParts.length > 1 && ampParts.every(p => emailRegex.test(p))) {
      groups.push(...ampParts)
    } else {
      groups.push(piece)
    }
  }

  const segments = []
  for (const group of groups) {
    if (!group || !group.trim()) continue
    // Within a group a comma may separate contacts or just affiliation parts, so
    // accumulate comma pieces until one carries an email/URL, then close a contact.
    let buffer = []
    for (const rawPart of group.split(',')) {
      const part = rawPart.trim()
      if (!part) continue
      buffer.push(part)
      if (emailRegex.test(part) || urlRegex.test(part)) {
        segments.push(buffer.join(', '))
        buffer = []
      }
    }
    if (buffer.length) segments.push(buffer.join(', '))
  }

  return segments.map(parseContact).filter(c => c.label || c.href)
}

export const licenseLabel = (license = '') => {
  if (!license) return ''
  const trimmed = license.trim()
  if (/^\d+(\.\d+)?$/.test(trimmed)) {
    return `CC-BY-${trimmed}`
  }
  const url = firstUrl(license)
  if (url) {
    const label = license.replace(url, '').trim()
    if (label) return label
    try {
      const u = new URL(url)
      const segments = u.pathname.split('/').filter(Boolean)
      const last = segments.length ? decodeURIComponent(segments[segments.length - 1]) : ''
      if (last) return last
      const host = u.hostname.replace(/^www\./, '')
      if (host) return host
    } catch {
      // ignore
    }
    try {
      const host = new URL(url).hostname.replace(/^www\./, '')
      return host || 'License'
    } catch {
      return 'License'
    }
  }
  return trimmed
}
