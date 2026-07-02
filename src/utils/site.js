// Shared site identity strings (single source of truth for the React side).
// index.html holds static copies of the title/meta tags for the initial load
// and social crawlers; keep them in sync with SITE_TITLE when it changes.
export const SITE_TITLE = 'FAIR Forward - Catalog of Open Source AI Datasets, Models & AI Systems'
export const SITE_NAME = 'FAIR Forward'
// Generic site-level description / social tags, mirrored from index.html. DetailPanel
// restores these when a project panel closes. Keep in sync with index.html.
export const SITE_DESCRIPTION = 'Reusable AI building blocks for global challenges across agriculture, language technology, climate action, energy, and more – built by our partners.'
export const SITE_URL = 'https://fair-forward.github.io/datasets/'
export const SITE_OG_IMAGE = 'https://fair-forward.github.io/datasets/img/fair_forward.png'
