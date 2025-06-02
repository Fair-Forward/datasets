#!/usr/bin/env python3
"""
Analytics Data Collector for Fair Forward Data Catalog
Collects analytics data from various sources and prepares it for dashboard generation
"""

import json
import os
import datetime
import argparse
import requests
from collections import defaultdict

class AnalyticsCollector:
    def __init__(self, config_file=None):
        self.config = self.load_config(config_file)
        self.events = []
    
    def load_config(self, config_file):
        """Load configuration from file or use defaults"""
        default_config = {
            'umami': {
                'enabled': False,
                'api_url': None,
                'website_id': None,
                'api_key': None
            },
            'github': {
                'enabled': True,
                'repo': None,
                'token': None
            },
            'local_storage': {
                'enabled': True,
                'file_path': 'analytics_data.json'
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    for key, value in user_config.items():
                        if key in default_config:
                            default_config[key].update(value)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def collect_from_umami(self):
        """Collect data from Umami Analytics API"""
        if not self.config['umami']['enabled']:
            return []
        
        try:
            # This is a placeholder - actual Umami API calls would go here
            # The Umami API structure depends on your specific setup
            print("Collecting from Umami (placeholder)")
            return []
        except Exception as e:
            print(f"Error collecting from Umami: {e}")
            return []
    
    def collect_from_github_pages(self):
        """Collect basic traffic data from GitHub Pages (if available)"""
        if not self.config['github']['enabled']:
            return []
        
        try:
            # GitHub doesn't provide detailed analytics via API for Pages
            # This is mainly for repository traffic data
            print("GitHub Pages analytics collection (limited)")
            return []
        except Exception as e:
            print(f"Error collecting from GitHub: {e}")
            return []
    
    def collect_from_local_storage(self):
        """Load existing analytics data from local storage"""
        file_path = self.config['local_storage']['file_path']
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} events from local storage")
                return data
        except Exception as e:
            print(f"Error loading local analytics data: {e}")
            return []
    
    def simulate_sample_data(self):
        """Generate sample analytics data for testing
        
        WARNING: This is for testing/development only!
        Should NEVER be used in production. Only activated with --sample flag.
        """
        sample_events = []
        
        # Generate sample data for the last 30 days
        for i in range(30):
            date = datetime.datetime.now() - datetime.timedelta(days=i)
            
            # Generate random events for each day
            for j in range(5, 25):  # 5-25 events per day
                event_types = ['page_view', 'card_view', 'link_click', 'search', 'filter_change']
                event_type = event_types[j % len(event_types)]
                
                event = {
                    'event_name': event_type,
                    'timestamp': date.isoformat(),
                    'session_id': f'sample_session_{i}_{j}',
                    'event_data': {}
                }
                
                if event_type == 'card_view':
                    event['event_data'] = {
                        'project_id': f'project_{j % 10}',
                        'title': f'Sample Project {j % 10}',
                        'region': ['Ghana', 'Kenya', 'India', 'Brazil'][j % 4],
                        'domains': [['Agriculture'], ['Health'], ['Education'], ['Climate']][j % 4],
                        'data_types': [['Images'], ['Text'], ['Tabular'], ['Geospatial']][j % 4],
                        'has_dataset': True,
                        'has_usecase': j % 2 == 0
                    }
                elif event_type == 'search':
                    search_terms = ['agriculture', 'health', 'climate', 'education', 'water']
                    event['event_data'] = {
                        'search_term': search_terms[j % len(search_terms)]
                    }
                elif event_type == 'filter_change':
                    filters = ['domainFilter:Agriculture', 'regionFilter:Ghana', 'dataTypeFilter:Images']
                    event['event_data'] = {
                        'filter_type': 'domainFilter',
                        'filter_value': 'Agriculture'
                    }
                elif event_type == 'link_click':
                    event['event_data'] = {
                        'link_type': 'dataset' if j % 2 == 0 else 'usecase',
                        'link_name': f'Sample Link {j}',
                        'href': f'https://example.com/dataset_{j}',
                        'project_id': f'project_{j % 10}'
                    }
                
                sample_events.append(event)
        
        print(f"Generated {len(sample_events)} sample events")
        return sample_events
    
    def create_monthly_aggregates(self, events):
        """Create monthly aggregated summaries for long-term storage"""
        monthly_data = defaultdict(lambda: {
            'total_events': 0,
            'unique_sessions': set(),
            'page_views': 0,
            'card_views': 0,
            'link_clicks': 0,
            'searches': 0,
            'filter_changes': 0,
            'popular_projects': defaultdict(int),
            'popular_domains': defaultdict(int),
            'popular_regions': defaultdict(int),
            'search_terms': defaultdict(int)
        })
        
        for event in events:
            try:
                # Parse timestamp to get year-month
                timestamp = event.get('timestamp', '')
                if not timestamp:
                    continue
                    
                date_obj = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                month_key = date_obj.strftime('%Y-%m')
                
                month_data = monthly_data[month_key]
                month_data['total_events'] += 1
                
                # Track unique sessions
                session_id = event.get('session_id')
                if session_id:
                    month_data['unique_sessions'].add(session_id)
                
                # Count event types
                event_name = event.get('event_name', '')
                if event_name in month_data:
                    month_data[event_name] += 1
                
                # Extract detailed data
                event_data = event.get('event_data', {})
                
                if event_name == 'card_view':
                    project_id = event_data.get('project_id')
                    if project_id:
                        month_data['popular_projects'][project_id] += 1
                    
                    domains = event_data.get('domains', [])
                    for domain in domains:
                        month_data['popular_domains'][domain] += 1
                    
                    region = event_data.get('region')
                    if region:
                        month_data['popular_regions'][region] += 1
                
                elif event_name == 'search':
                    search_term = event_data.get('search_term')
                    if search_term:
                        month_data['search_terms'][search_term] += 1
                        
            except Exception as e:
                print(f"Warning: Error processing event for aggregation: {e}")
                continue
        
        # Convert sets to counts and defaultdicts to regular dicts
        aggregated = {}
        for month, data in monthly_data.items():
            aggregated[month] = {
                'total_events': data['total_events'],
                'unique_sessions': len(data['unique_sessions']),
                'page_views': data['page_views'],
                'card_views': data['card_views'],
                'link_clicks': data['link_clicks'],
                'searches': data['searches'],
                'filter_changes': data['filter_changes'],
                'popular_projects': dict(data['popular_projects']),
                'popular_domains': dict(data['popular_domains']),
                'popular_regions': dict(data['popular_regions']),
                'search_terms': dict(data['search_terms'])
            }
        
        return aggregated
    
    def manage_historical_data(self, all_events):
        """Manage data retention with monthly aggregates for historical data"""
        # Separate recent (90 days) and historical data
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=90)
        cutoff_str = cutoff_date.isoformat()
        
        recent_events = []
        historical_events = []
        
        for event in all_events:
            timestamp = event.get('timestamp', '')
            if timestamp >= cutoff_str:
                recent_events.append(event)
            else:
                historical_events.append(event)
        
        # Create monthly aggregates for historical data
        historical_aggregates = {}
        if historical_events:
            historical_aggregates = self.create_monthly_aggregates(historical_events)
            print(f"Created aggregates for {len(historical_aggregates)} months from {len(historical_events)} historical events")
        
        # Load existing aggregates if they exist
        aggregates_file = getattr(self, 'output_file', 'analytics_data.json').replace('.json', '_monthly.json')
        if os.path.exists(aggregates_file):
            try:
                with open(aggregates_file, 'r', encoding='utf-8') as f:
                    existing_aggregates = json.load(f)
                    # Merge with new aggregates (new data takes precedence)
                    for month, data in existing_aggregates.items():
                        if month not in historical_aggregates:
                            historical_aggregates[month] = data
                    print(f"Merged with existing monthly aggregates")
            except Exception as e:
                print(f"Warning: Could not load existing aggregates: {e}")
        
        # Save monthly aggregates
        if historical_aggregates:
            try:
                with open(aggregates_file, 'w', encoding='utf-8') as f:
                    json.dump(historical_aggregates, f, indent=2, ensure_ascii=False)
                print(f"Monthly aggregates saved to {aggregates_file}")
            except Exception as e:
                print(f"Error saving monthly aggregates: {e}")
        
        return recent_events, historical_aggregates
    
    def collect_all(self, include_sample=False):
        """Collect analytics data from all configured sources"""
        all_events = []
        
        # FIRST: Load existing data to preserve history
        output_file = getattr(self, 'output_file', 'analytics_data.json')
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    all_events.extend(existing_data)
                    print(f"Loaded {len(existing_data)} existing events from {output_file}")
            except Exception as e:
                print(f"Warning: Could not load existing data: {e}")
        
        # Collect from various sources (new data only)
        new_events = []
        new_events.extend(self.collect_from_local_storage())
        new_events.extend(self.collect_from_umami())
        new_events.extend(self.collect_from_github_pages())
        
        # Add sample data if requested (useful for testing)
        if include_sample:
            new_events.extend(self.simulate_sample_data())
        
        # Combine existing and new events
        all_events.extend(new_events)
        print(f"Added {len(new_events)} new events")
        
        # Remove duplicates and sort by timestamp
        seen = set()
        unique_events = []
        for event in all_events:
            # Create a more comprehensive key for deduplication
            event_key = (
                event.get('timestamp'), 
                event.get('session_id'), 
                event.get('event_name'),
                str(event.get('event_data', {}))  # Include event data in dedup key
            )
            if event_key not in seen:
                seen.add(event_key)
                unique_events.append(event)
        
        # Sort by timestamp
        unique_events.sort(key=lambda x: x.get('timestamp', ''))
        
        # Use new historical data management
        recent_events, historical_aggregates = self.manage_historical_data(unique_events)
        
        # Store both recent events and aggregates for dashboard generation
        self.events = recent_events
        self.monthly_aggregates = historical_aggregates
        
        print(f"Keeping {len(recent_events)} recent events (last 90 days)")
        if historical_aggregates:
            print(f"Archived {len(historical_aggregates)} months of historical data")
        
        return recent_events
    
    def save_data(self, output_file):
        """Save collected analytics data to file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2, ensure_ascii=False)
            print(f"Analytics data saved to {output_file}")
        except Exception as e:
            print(f"Error saving analytics data: {e}")
    
    def get_summary(self):
        """Get a summary of collected data"""
        if not self.events:
            return "No analytics data collected"
        
        event_types = defaultdict(int)
        for event in self.events:
            event_types[event.get('event_name', 'unknown')] += 1
        
        summary = f"""
Analytics Data Summary:
- Total events: {len(self.events)}
- Event types: {dict(event_types)}
- Date range: {self.events[0].get('timestamp', 'unknown')} to {self.events[-1].get('timestamp', 'unknown')}
"""
        return summary

def main():
    parser = argparse.ArgumentParser(description='Collect analytics data')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--output', type=str, default='analytics_data.json', 
                       help='Output file for analytics data')
    parser.add_argument('--sample', action='store_true', 
                       help='Include sample data for testing')
    parser.add_argument('--dashboard', action='store_true',
                       help='Also generate dashboard after collecting data')
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = AnalyticsCollector(args.config)
    
    # Set output file for data accumulation
    collector.output_file = args.output
    
    # Collect data
    events = collector.collect_all(include_sample=args.sample)
    
    # Save data
    collector.save_data(args.output)
    
    # Print summary
    print(collector.get_summary())
    
    # Generate dashboard if requested
    if args.dashboard:
        try:
            import subprocess
            dashboard_cmd = ['python', 'analytics_dashboard.py', '--input', args.output]
            subprocess.run(dashboard_cmd, check=True)
            print("Dashboard generated successfully")
        except Exception as e:
            print(f"Error generating dashboard: {e}")

if __name__ == "__main__":
    main() 