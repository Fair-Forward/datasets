export const withBasePath = (path = '') => {
  const normalized = path.startsWith('/') ? path.slice(1) : path

  // Vite is configured with `base: './'` for GitHub Pages, which makes BASE_URL relative.
  // Relative paths break when the SPA is on a nested route (e.g. /insights), so we resolve
  // against the document base instead.
  if (typeof document !== 'undefined' && document.baseURI) {
    return new URL(normalized, document.baseURI).pathname
  }

  const rawBase = import.meta.env.BASE_URL || '/'
  const basePath = rawBase.endsWith('/') ? rawBase : `${rawBase}/`
  return `${basePath}${normalized}`
}

export default withBasePath

