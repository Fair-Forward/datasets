const ProjectCard = ({ project, onClick }) => {
  const { title, description, sdgs, data_types, image, dataset_links = [], usecase_links = [], is_lacuna } = project

  const cardClasses = [
    'card',
    dataset_links.length > 0 ? 'has-dataset' : '',
    usecase_links.length > 0 ? 'has-usecase' : '',
    is_lacuna ? 'has-lacuna' : ''
  ].filter(Boolean).join(' ')

  // Truncate description
  const maxLength = 200
  const truncatedDesc = description.length > maxLength 
    ? description.substring(0, maxLength) + '...'
    : description

  return (
    <div className={cardClasses} onClick={() => onClick(project)}>
      {image && (
        <div className="card-image">
          <img src={image} alt={title} />
        </div>
      )}
      
      <div className="card-header">
        {sdgs.length > 0 && (
          <div className="domain-badges">
            {sdgs.slice(0, 3).map(sdg => (
              <span key={sdg} className="domain-badge">
                {sdg}
              </span>
            ))}
          </div>
        )}
        <h3>{title}</h3>
        
        {is_lacuna && (
          <div className="lacuna-badge">
            <i className="fas fa-star"></i> Lacuna Fund
          </div>
        )}
      </div>
      
      <div className="card-body">
        <div className="card-description">
          <div className="description-text collapsed">
            {truncatedDesc}
          </div>
          <div className="details-link">
            <i className="fas fa-arrow-right-long"></i>
            <span>Click card to see details</span>
          </div>
        </div>
        
        <div className="tags" style={{ display: 'none' }}>
          {sdgs.map(sdg => (
            <span key={sdg} className="tag" data-filter={sdg}>
              {sdg}
            </span>
          ))}
          {data_types.map(dt => (
            <span key={dt} className="tag" data-filter={dt}>
              {dt}
            </span>
          ))}
        </div>
        
        <div className="hidden-links" style={{ display: 'none' }}>
          {dataset_links.map((link, i) => (
            <a key={i} href={link.url} target="_blank" rel="noopener noreferrer" 
               className="btn btn-primary hidden-link" 
               data-link-type="dataset">
              {link.name || `Dataset ${i + 1}`}
            </a>
          ))}
          {usecase_links.map((link, i) => (
            <a key={i} href={link.url} target="_blank" rel="noopener noreferrer"
               className="btn btn-primary hidden-link"
               data-link-type="usecase">
              {link.name || `Use Case ${i + 1}`}
            </a>
          ))}
        </div>
      </div>
      
      <div className="card-footer">
        <div className="data-type-chips footer-chips">
          {data_types.map(dt => (
            <span key={dt} className="data-type-chip" data-filter={dt}>
              {dt}
            </span>
          ))}
        </div>
        {project.license && (
          <div className="license-tag">
            <i className="fas fa-copyright"></i>
            {' '}
            {project.license}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProjectCard

