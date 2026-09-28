import { withBasePath } from '../utils/basePath'

const Footer = () => {
  return (
    <footer>
      <div className="footer-content">
        <p className="footer-imprint">&copy; {new Date().getFullYear()} Fair Forward - Artificial Intelligence for All | A project by GIZ</p>
        <div className="footer-notes">
          <p className="footer-secondary">
            <a href="https://github.com/Fair-Forward/datasets" target="_blank" rel="noopener noreferrer">
              Contribute to the Source Code on GitHub <i className="fab fa-github" aria-hidden="true"></i>
            </a>
            {' · '}
            {/* Static page under public/, not a router route -- plain href, not <Link>. */}
            <a href={withBasePath('privacy/')}>Privacy</a>
          </p>
          <p className="footer-secondary">
            For technical questions/feedback{' '}
            <a href="https://github.com/Fair-Forward/datasets/issues" target="_blank" rel="noopener noreferrer">
              open an issue on Github
            </a>
            {' '}or contact{' '}
            <a href="mailto:jonas.nothnagel@gmail.com">
              Jonas Nothnagel
            </a>.
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
