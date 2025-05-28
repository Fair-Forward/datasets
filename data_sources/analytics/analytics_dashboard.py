#!/usr/bin/env python3
"""
Analytics Dashboard Generator for Fair Forward Data Catalog
Generates a simple analytics dashboard from stored events
"""

import json
import os
import datetime
from collections import defaultdict, Counter
import argparse

def load_analytics_data(data_file):
    """Load analytics data from JSON file"""
    if not os.path.exists(data_file):
        return []
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading analytics data: {e}")
        return []

def analyze_events(events):
    """Analyze events and generate statistics"""
    stats = {
        'total_events': len(events),
        'unique_sessions': len(set(event.get('session_id', '') for event in events)),
        'event_types': Counter(),
        'popular_projects': Counter(),
        'popular_domains': Counter(),
        'popular_data_types': Counter(),
        'popular_regions': Counter(),
        'search_terms': Counter(),
        'filter_usage': Counter(),
        'external_links': Counter(),
        'daily_activity': defaultdict(int),
        'hourly_activity': defaultdict(int)
    }
    
    for event in events:
        event_name = event.get('event_name', 'unknown')
        event_data = event.get('event_data', {})
        timestamp = event.get('timestamp', '')
        
        stats['event_types'][event_name] += 1
        
        # Parse timestamp for time-based analysis
        try:
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
            hour = dt.hour
            stats['daily_activity'][date_str] += 1
            stats['hourly_activity'][hour] += 1
        except:
            pass
        
        # Analyze specific event types
        if event_name == 'card_view':
            project_id = event_data.get('project_id')
            if project_id:
                stats['popular_projects'][project_id] += 1
            
            domains = event_data.get('domains', [])
            for domain in domains:
                stats['popular_domains'][domain] += 1
            
            data_types = event_data.get('data_types', [])
            for data_type in data_types:
                stats['popular_data_types'][data_type] += 1
            
            region = event_data.get('region')
            if region:
                stats['popular_regions'][region] += 1
        
        elif event_name == 'search':
            search_term = event_data.get('search_term', '').lower()
            if search_term:
                stats['search_terms'][search_term] += 1
        
        elif event_name == 'filter_change':
            filter_type = event_data.get('filter_type')
            filter_value = event_data.get('filter_value')
            if filter_type and filter_value:
                stats['filter_usage'][f"{filter_type}:{filter_value}"] += 1
        
        elif event_name == 'external_link_click':
            href = event_data.get('href')
            if href:
                stats['external_links'][href] += 1
    
    return stats

def generate_dashboard_html(stats, output_file):
    """Generate HTML dashboard"""
    
    # Get top items for each category
    top_projects = stats['popular_projects'].most_common(10)
    top_domains = stats['popular_domains'].most_common(10)
    top_data_types = stats['popular_data_types'].most_common(10)
    top_regions = stats['popular_regions'].most_common(5)
    top_searches = stats['search_terms'].most_common(10)
    top_filters = stats['filter_usage'].most_common(10)
    top_external_links = stats['external_links'].most_common(10)
    
    # Generate daily activity chart data
    daily_data = sorted(stats['daily_activity'].items())
    daily_labels = [item[0] for item in daily_data[-30:]]  # Last 30 days
    daily_values = [item[1] for item in daily_data[-30:]]
    
    # Generate hourly activity chart data
    hourly_data = [(hour, stats['hourly_activity'][hour]) for hour in range(24)]
    hourly_labels = [f"{hour:02d}:00" for hour in range(24)]
    hourly_values = [stats['hourly_activity'][hour] for hour in range(24)]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fair Forward Analytics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8fafc;
            color: #1e293b;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            text-align: center;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 600;
            color: #3b5998;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #64748b;
            font-size: 0.9rem;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        .chart-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: #1e293b;
        }}
        .tables-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .table-container {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }}
        .table-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 15px;
            color: #1e293b;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            text-align: left;
            padding: 8px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #f8fafc;
            font-weight: 600;
            color: #475569;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #3b5998;
            text-decoration: none;
            font-weight: 500;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
        .last-updated {{
            text-align: center;
            color: #64748b;
            font-size: 0.9rem;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← Back to Data Catalog</a>
        
        <div class="header">
            <h1>Fair Forward Analytics Dashboard</h1>
            <p>Usage statistics and insights for the data catalog</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_events']:,}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['unique_sessions']:,}</div>
                <div class="stat-label">Unique Sessions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['event_types'].get('card_view', 0):,}</div>
                <div class="stat-label">Dataset Views</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['event_types'].get('link_click', 0):,}</div>
                <div class="stat-label">Link Clicks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['event_types'].get('search', 0):,}</div>
                <div class="stat-label">Searches</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">Daily Activity (Last 30 Days)</div>
                <canvas id="dailyChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <div class="chart-title">Hourly Activity</div>
                <canvas id="hourlyChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="tables-grid">
            <div class="table-container">
                <div class="table-title">Most Popular Projects</div>
                <table>
                    <thead>
                        <tr><th>Project ID</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{project}</td><td>{count}</td></tr>" for project, count in top_projects)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <div class="table-title">Popular Domains</div>
                <table>
                    <thead>
                        <tr><th>Domain</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{domain}</td><td>{count}</td></tr>" for domain, count in top_domains)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <div class="table-title">Popular Data Types</div>
                <table>
                    <thead>
                        <tr><th>Data Type</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{data_type}</td><td>{count}</td></tr>" for data_type, count in top_data_types)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <div class="table-title">Popular Regions</div>
                <table>
                    <thead>
                        <tr><th>Region</th><th>Views</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{region}</td><td>{count}</td></tr>" for region, count in top_regions)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <div class="table-title">Top Search Terms</div>
                <table>
                    <thead>
                        <tr><th>Search Term</th><th>Count</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{term}</td><td>{count}</td></tr>" for term, count in top_searches)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <div class="table-title">Filter Usage</div>
                <table>
                    <thead>
                        <tr><th>Filter</th><th>Count</th></tr>
                    </thead>
                    <tbody>
                        {"".join(f"<tr><td>{filter_item}</td><td>{count}</td></tr>" for filter_item, count in top_filters)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="last-updated">
            Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
    </div>
    
    <script>
        // Daily Activity Chart
        const dailyCtx = document.getElementById('dailyChart').getContext('2d');
        new Chart(dailyCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(daily_labels)},
                datasets: [{{
                    label: 'Events',
                    data: {json.dumps(daily_values)},
                    borderColor: '#3b5998',
                    backgroundColor: 'rgba(59, 89, 152, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        // Hourly Activity Chart
        const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
        new Chart(hourlyCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(hourly_labels)},
                datasets: [{{
                    label: 'Events',
                    data: {json.dumps(hourly_values)},
                    backgroundColor: 'rgba(59, 89, 152, 0.6)',
                    borderColor: '#3b5998',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Dashboard generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate analytics dashboard')
    parser.add_argument('--input', type=str, default='analytics_data.json', 
                       help='Input analytics data file')
    parser.add_argument('--output', type=str, default='docs/analytics.html', 
                       help='Output HTML dashboard file')
    
    args = parser.parse_args()
    
    # Load analytics data
    events = load_analytics_data(args.input)
    
    if not events:
        print("No analytics data found. Creating empty dashboard.")
        events = []
    
    # Analyze events
    stats = analyze_events(events)
    
    # Generate dashboard
    generate_dashboard_html(stats, args.output)
    
    print(f"Analytics dashboard generated with {len(events)} events")

if __name__ == "__main__":
    main() 