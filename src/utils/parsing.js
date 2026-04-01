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

export const parseContact = (contact = '') => {
  if (!contact) return { label: '', href: null }
  const emailMatch = contact.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)
  const urlMatch = contact.match(urlRegex)

  const beforeComma = contact.split(',')[0].trim()
  const beforeParen = contact.split('(')[0].trim()
  const baseLabel = cleanLabel(beforeComma || beforeParen || contact)

  if (emailMatch) {
    const email = emailMatch[0]
    const label = cleanLabel(baseLabel.replace(email, '').trim()) || baseLabel || email
    return { label, href: `mailto:${email}` }
  }

  if (urlMatch) {
    const url = urlMatch[0]
    const label = cleanLabel(baseLabel.replace(url, '').trim()) || baseLabel || url
    return { label, href: url }
  }

  return { label: cleanLabel(contact), href: null }
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
