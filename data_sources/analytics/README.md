# Fair Forward Analytics System

## Overview
The analytics system tracks user interactions on the Fair Forward Data Catalog website and generates usage dashboards. It's designed to be privacy-focused and works entirely with local data storage.

## How It Works

### 1. Data Collection (Browser)
- **Script**: `docs/umami-analytics.js`
- **Storage**: Browser localStorage (key: `ff_analytics_events`)
- **Tracks**: Card views, link clicks, searches, filter changes, page views
- **Privacy**: All data stays in user's browser until manually exported

### 2. Data Processing (Server)
- **Script**: `collect_analytics.py`
- **Function**: Aggregates events, manages data retention (90 days + monthly archives)
- **Output**: JSON file with processed analytics data

### 3. Dashboard Generation
- **Script**: `analytics_dashboard.py`
- **Function**: Creates HTML dashboard with charts and statistics
- **Output**: `docs/analytics.html` (deployed to GitHub Pages)

## Current Status

✅ **Analytics tracking is ENABLED** (as of latest update)
✅ **Automated daily dashboard updates** (6 AM UTC)
✅ **No Git conflicts** (analytics data stored in /tmp, only dashboard HTML committed)

## Data Collection Status

The dashboard currently shows zeros because:
1. Analytics tracking was recently enabled
2. No real user data has been collected yet
3. Users need to visit the website for data to accumulate

## Testing Analytics

To test with sample data:
```bash
# Generate sample analytics data
python data_sources/analytics/collect_analytics.py --sample --output /tmp/test_analytics.json

# Generate test dashboard
python data_sources/analytics/analytics_dashboard.py --input /tmp/test_analytics.json --output /tmp/test_dashboard.html
```

## Collecting Real Browser Data

To collect real analytics data from browser localStorage:

1. **Visit the website** and interact with it (click cards, search, filter)
2. **Open browser console** (F12)
3. **Export localStorage data**:
   ```javascript
   // Get stored analytics events
   const events = JSON.parse(localStorage.getItem('ff_analytics_events') || '[]');
   console.log('Analytics events:', events);
   
   // Download as JSON file
   const blob = new Blob([JSON.stringify(events, null, 2)], {type: 'application/json'});
   const url = URL.createObjectURL(blob);
   const a = document.createElement('a');
   a.href = url;
   a.download = 'analytics_events.json';
   a.click();
   ```
4. **Place the downloaded file** in `data_sources/analytics/analytics_data.json`
5. **Run the analytics workflow** to generate updated dashboard

## Automated Workflow

The GitHub Action runs daily and:
1. Collects analytics data (currently empty until real users visit)
2. Generates updated dashboard
3. Commits only if dashboard changed
4. Deploys to GitHub Pages

## Data Retention

- **Recent events**: Last 90 days (full detail)
- **Historical data**: Monthly aggregates (indefinite retention)
- **Browser storage**: Last 100 events per user

## Privacy & Compliance

- ✅ No external tracking services
- ✅ No personal data collection
- ✅ Data stays in user's browser
- ✅ No cookies or persistent identifiers
- ✅ GDPR compliant (local storage only) 