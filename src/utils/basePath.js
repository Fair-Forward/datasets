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

export default withBasePath

