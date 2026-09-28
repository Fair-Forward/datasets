import Header from './Header'
import { SITE_TITLE } from '../utils/site'

const count = (n) => n.toLocaleString('en')

const CatalogHeader = ({ totals, search, onSearchChange, onBrowse }) => (
  <header>
    <Header />

    <section className="hero">
      <div className="hero-inner">
        <h1 className="hero-title">{SITE_TITLE}</h1>
        <p className="hero-lead">
          Reusable AI building blocks for global challenges across agriculture,
          language technology, climate action, energy, and more – built by our partners.
        </p>

        {/* Filtering is live as you type; submitting takes you to the results. */}
        <form
          className="hero-search"
          role="search"
          onSubmit={(e) => { e.preventDefault(); onBrowse?.() }}
        >
          <label htmlFor="catalog-search" className="sr-only">Search datasets and use cases</label>
          <i className="fas fa-magnifying-glass" aria-hidden="true"></i>
          <input
            id="catalog-search"
            type="search"
            className="hero-search-input"
            placeholder="Search datasets and use cases"
            value={search || ''}
            onChange={(e) => onSearchChange?.(e.target.value)}
            autoComplete="off"
          />
        </form>

        {/* The whole catalogue's totals; the counts for the current filter sit
            above the results. */}
        {totals && (
          <ul className="figures-list hero-figures" aria-label="The catalog in numbers">
            <li className="figure">
              <span className="figure-number">{count(totals.total_projects)}</span>
              <span className="figure-label">projects</span>
            </li>
            <li className="figure">
              <span className="figure-number">{count(totals.total_datasets)}</span>
              <span className="figure-label">datasets</span>
            </li>
            <li className="figure">
              <span className="figure-number">{count(totals.total_usecases)}</span>
              <span className="figure-label">pilots and use cases</span>
            </li>
            <li className="figure">
              <span className="figure-number">{count(totals.total_countries)}</span>
              <span className="figure-label">countries</span>
            </li>
          </ul>
        )}
      </div>
    </section>
  </header>
)

export default CatalogHeader
