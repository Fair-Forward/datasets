const rawBase = import.meta.env.BASE_URL || '/'
const basePath = rawBase.endsWith('/') ? rawBase : `${rawBase}/`

export const withBasePath = (path = '') => {
  const normalized = path.startsWith('/') ? path.slice(1) : path
  return `${basePath}${normalized}`
}

export default withBasePath

