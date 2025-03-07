import { useState, useEffect } from 'react'
import './App.css'

function DataCard({ item }) {
  const [expanded, setExpanded] = useState(false);
  
  // Handle missing or undefined values
  const title = item.Title || 'No Title';
  const description = item.Description || '';
  const dataType = item['Data Type'] || '';
  const domain = item.Domain || item['SDG/Domain'] || '';
  const region = item['Country/Region'] || '';
  
  return (
    <div className="card">
      <div className="card-header">
        <h3>{title}</h3>
        {domain && <div className="domain-badge">{domain}</div>}
      </div>
      <div className="card-body">
        <p className={`description ${expanded ? 'expanded' : 'collapsed'}`}>
          {description}
        </p>
        {description.length > 100 && (
          <button 
            className="read-more" 
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Read less' : 'Read more'}
          </button>
        )}
        {dataType && <div className="data-type">Data Type: {dataType}</div>}
        {region && <div className="region">Region: {region}</div>}
      </div>
    </div>
  )
}

function App() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch('../data.json')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(jsonData => {
        console.log('Loaded data:', jsonData);
        setData(jsonData);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading data:', error);
        setError(error.message);
        setLoading(false);
      });
  }, []);
  
  if (loading) return <div className="loading">Loading data...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!data.length) return <div className="empty">No data available</div>;

  return (
    <div className="container">
      <header>
        <h1>Data Catalog</h1>
        <p>Exploring datasets and use cases</p>
      </header>
      
      <main>
        <div className="grid">
          {data.map((item, index) => (
            <DataCard key={index} item={item} />
          ))}
        </div>
      </main>
    </div>
  )
}

export default App