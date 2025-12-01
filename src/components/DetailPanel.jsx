import { useState, useEffect } from 'react'

const DetailPanel = ({ project, onClose }) => {
  const [markdownContent, setMarkdownContent] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!project) return

    // Load markdown files
    const loadMarkdown = async () => {
      try {
        const files = {
          description: 'description.md',
          data_characteristics: 'data_characteristics.md',
          model_characteristics: 'model_characteristics.md',
          how_to_use: 'how_to_use.md'
        }

        const content = {}
        
        for (const [key, filename] of Object.entries(files)) {
          try {
            const response = await fetch(`/public/projects/${project.id}/docs/${filename}`)
            if (response.ok) {
              content[key] = await response.text()
            }
          } catch (err) {
            console.log(`Could not load ${filename}:`, err)
          }
        }

        setMarkdownContent(content)
        setLoading(false)
      } catch (err) {
        console.error('Error loading markdown:', err)
        setLoading(false)
      }
    }

    loadMarkdown()
  }, [project])

  if (!project) return null

  return (
    <>
      <div className="panel-overlay" onClick={onClose}></div>
      <div className="detail-panel">
        <div className="detail-panel-header">
          <button className="close-panel-btn" onClick={onClose}>
            <i className="fas fa-times"></i>
          </button>
          <h2>{project.title}</h2>
        </div>
        
        <div className="detail-panel-content">
          {loading ? (
            <div className="panel-loader">
              <div className="loader-spinner"></div>
              <p>Loading details...</p>
            </div>
          ) : (
            <div className="panel-data">
              {/* Description */}
              {(markdownContent.description || project.description) && (
                <section className="detail-section">
                  <h3><i className="fas fa-info-circle"></i> Description</h3>
                  <div className="detail-content">
                    {markdownContent.description || project.description}
                  </div>
                </section>
              )}

              {/* Links */}
              <section className="detail-section">
                <h3><i className="fas fa-link"></i> Links</h3>
                <div className="detail-links">
                  {project.dataset_links.map((link, i) => (
                    <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" 
                       className="btn btn-primary">
                      <i className="fas fa-database"></i> {link.name}
                    </a>
                  ))}
                  {project.usecase_links.map((link, i) => (
                    <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
                       className="btn btn-primary">
                      <i className="fas fa-brain"></i> {link.name}
                    </a>
                  ))}
                </div>
              </section>

              {/* Data Characteristics */}
              {markdownContent.data_characteristics && (
                <section className="detail-section">
                  <h3><i className="fas fa-table"></i> Data Characteristics</h3>
                  <div className="detail-content">
                    {markdownContent.data_characteristics}
                  </div>
                </section>
              )}

              {/* Model Characteristics */}
              {markdownContent.model_characteristics && (
                <section className="detail-section">
                  <h3><i className="fas fa-robot"></i> Model/Use Case Characteristics</h3>
                  <div className="detail-content">
                    {markdownContent.model_characteristics}
                  </div>
                </section>
              )}

              {/* How to Use */}
              {markdownContent.how_to_use && (
                <section className="detail-section">
                  <h3><i className="fas fa-code"></i> How to Use</h3>
                  <div className="detail-content">
                    {markdownContent.how_to_use}
                  </div>
                </section>
              )}

              {/* Metadata */}
              <section className="detail-section">
                <h3><i className="fas fa-tags"></i> Metadata</h3>
                <div className="detail-metadata">
                  {project.countries.length > 0 && (
                    <div className="metadata-item">
                      <strong>Countries:</strong> {project.countries.join(', ')}
                    </div>
                  )}
                  {project.sdgs.length > 0 && (
                    <div className="metadata-item">
                      <strong>SDGs:</strong> {project.sdgs.join(', ')}
                    </div>
                  )}
                  {project.data_types.length > 0 && (
                    <div className="metadata-item">
                      <strong>Data Types:</strong> {project.data_types.join(', ')}
                    </div>
                  )}
                  {project.license && (
                    <div className="metadata-item">
                      <strong>License:</strong> {project.license}
                    </div>
                  )}
                  {project.contact && (
                    <div className="metadata-item">
                      <strong>Contact:</strong> {project.contact}
                    </div>
                  )}
                </div>
              </section>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default DetailPanel

