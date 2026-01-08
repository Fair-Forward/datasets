// Compute the base path ONCE at module load time, before any client-side routing.
// This ensures we capture the true deployment base path.
const computeBasePath = () => {
  if (typeof document !== 'undefined') {
    // Method 1: Use the script element's resolved URL
    const scriptEl = document.querySelector?.('script[type="module"][src]')
    const scriptSrc = scriptEl?.src
    if (scriptSrc && scriptSrc.includes('/assets/')) {
      return scriptSrc.split('/assets/')[0] + '/'
    }

    // Method 2: Use current location at module init time (before routing changes it)
    // On GitHub Pages, after 404.html redirect, we're at the correct base
    const pathname = window.location.pathname
    // Extract base: /datasets/anything -> /datasets/
    const match = pathname.match(/^(\/[^/]+\/)/)
    if (match) {
      return match[1]
    }
  }

  // Fallback for local dev
  return '/'
}

// Cache the base path at module load time
const BASE_PATH = computeBasePath()

export const withBasePath = (path = '') => {
  const normalized = path.startsWith('/') ? path.slice(1) : path
  return `${BASE_PATH}${normalized}`
}

export default withBasePath

