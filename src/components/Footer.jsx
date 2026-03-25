const Footer = () => {
  return (
    <footer>
      <div className="footer-content">
        <p>&copy; {new Date().getFullYear()} Fair Forward - Artificial Intelligence for All | A project by GIZ</p>
        <p className="footer-secondary">
          <a href="https://github.com/Fair-Forward/datasets" target="_blank" rel="noopener noreferrer">
            Contribute to the Source Code on GitHub <i className="fab fa-github"></i>
          </a>
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
    </footer>
  )
}

export default Footer
