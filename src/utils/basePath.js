// Compute the base path ONCE at module load time, before any client-side routing.
const computeBasePath = () => {
  if (typeof window === 'undefined') return '/'
  
  // On GitHub Pages (*.github.io), extract the repo name as base path
  const hostname = window.location.hostname
  if (hostname.endsWith('.github.io')) {
    const pathname = window.location.pathname
    // Extract first path segment: /datasets/... -> /datasets/
    const match = pathname.match(/^\/([^/]+)/)
    if (match) {
      return `/${match[1]}/`
    }
  }
  
  // Local development
  return '/'
}

// Cache the base path at module load time
const BASE_PATH = computeBasePath()

export const withBasePath = (path = '') => {
  const normalized = path.startsWith('/') ? path.slice(1) : path
  return `${BASE_PATH}${normalized}`
}

/**
 * Resolve hrefs for links served from this site (e.g. /projects/.../documents/x.pdf on GitHub Pages).
 * Leaves http(s), mailto, tel, and hash-only anchors unchanged.
 */
export const resolvePublicHref = (href) => {
  if (!href) return href
  if (href.startsWith('#')) return href
  if (href.startsWith('mailto:') || href.startsWith('tel:')) return href
  if (href.startsWith('http://') || href.startsWith('https://')) return href
  if (href.startsWith('/')) return withBasePath(href)
  return href
}

export default withBasePath

