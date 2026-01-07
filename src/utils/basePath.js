export const withBasePath = (path = '') => {
  const normalized = path.startsWith('/') ? path.slice(1) : path

  // Vite is configured with `base: './'` for GitHub Pages, which makes BASE_URL relative.
  // To avoid route-dependent resolution (document URL changes with client-side navigation),
  // derive the stable site root from the bundled module script URL (e.g. .../assets/index.js).
  if (typeof document !== 'undefined') {
    const scriptEl = document.querySelector?.('script[type="module"][src]')
    const scriptSrc = scriptEl?.src
    if (scriptSrc && scriptSrc.includes('/assets/')) {
      const base = scriptSrc.split('/assets/')[0] + '/'
      return new URL(normalized, base).pathname
    }
  }

  const rawBase = import.meta.env.BASE_URL || '/'
  const basePath = rawBase.endsWith('/') ? rawBase : `${rawBase}/`
  return `${basePath}${normalized}`
}

export default withBasePath

