# Fair Forward Analytics System

## Overview
The analytics system tracks user interactions on the Fair Forward Data Catalog website and generates usage dashboards. It's designed to be privacy-focused and works entirely with local data storage.

## Current Setup: Local-Only Analytics

### How It Works

#### 1. Data Collection (Browser)
- **Script**: `docs/umami-analytics.js`
- **Storage**: Browser localStorage (key: `ff_analytics_events`)
- **Tracks**: Card views, link clicks, searches, filter changes, page views
- **Privacy**: All data stays in user's browser until manually exported

#### 2. Data Processing (Server)
- **Script**: `collect_analytics.py`
- **Function**: Aggregates events, manages data retention (90 days + monthly archives)
- **Output**: JSON file with processed analytics data

#### 3. Dashboard Generation
- **Script**: `analytics_dashboard.py`
- **Function**: Creates HTML dashboard from processed data
- **Output**: `docs/analytics.html` (publicly accessible)

## Analytics Server Options

### Current: Local-Only (No Server)

**Pros:**
- ✅ Complete privacy (no external tracking)
- ✅ No server costs or maintenance
- ✅ GDPR compliant by design
- ✅ Works offline
- ✅ No cookies or external dependencies

**Cons:**
- ❌ Limited data collection (only from engaged users)
- ❌ Data loss if browser storage cleared
- ❌ No real-time insights
- ❌ Manual data export required
- ❌ No cross-device tracking

### Option 1: Self-Hosted Umami Server

**Setup Requirements:**
```bash
# Using Docker (recommended)
docker run -d \
  --name umami \
  -p 3000:3000 \
  -e DATABASE_URL=postgresql://username:password@host:port/database \
  ghcr.io/umami-software/umami:postgresql-latest

# Or using Railway/Vercel/DigitalOcean
# 1. Deploy Umami instance
# 2. Create website in Umami dashboard
# 3. Get website ID and API endpoint
```

**Configuration:**
```javascript
const analyticsConfig = {
    websiteId: 'your-umami-website-id',
    apiEndpoint: 'https://your-umami-instance.com/api/send',
    trackClicks: true,
    trackViews: true,
    trackFilters: true,
    debug: false
};
```

**Pros:**
- ✅ Real-time analytics
- ✅ Professional dashboard
- ✅ Data persistence
- ✅ Cross-device tracking
- ✅ Still privacy-focused (self-hosted)
- ✅ No data shared with third parties

**Cons:**
- ❌ Server hosting costs (~$5-20/month)
- ❌ Maintenance overhead
- ❌ Requires database setup
- ❌ More complex deployment

**Estimated Costs:**
- Railway/Vercel: $5-10/month
- DigitalOcean Droplet: $6-12/month
- AWS/GCP: $10-25/month

### Option 2: Hybrid Approach

Keep local storage as primary, add optional Umami for power users:

```javascript
const analyticsConfig = {
    // Optional Umami (only if configured)
    websiteId: process.env.UMAMI_WEBSITE_ID || null,
    apiEndpoint: process.env.UMAMI_API_ENDPOINT || null,
    
    // Always use local storage as backup
    useLocalStorage: true,
    
    // Prompt users to share data
    prompt: true
};
```

### Option 3: Serverless Analytics

Use GitHub Issues API or Google Sheets as a simple analytics backend:

```javascript
// Send analytics to GitHub Issues (for small scale)
const sendToGitHub = async (eventData) => {
    await fetch('https://api.github.com/repos/your-org/analytics/issues', {
        method: 'POST',
        headers: {
            'Authorization': 'token YOUR_TOKEN',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: `Analytics: ${eventData.event_name}`,
            body: JSON.stringify(eventData, null, 2),
            labels: ['analytics', 'automated']
        })
    });
};
```

## Recommendations

### For Current Phase (MVP):
**Keep local-only approach** with the new export functionality. This gives you:
- Zero infrastructure costs
- Complete privacy compliance
- Basic usage insights
- Foundation for future upgrades

### For Growth Phase:
**Add self-hosted Umami** when you have:
- Regular users (>100/month)
- Budget for hosting ($10-20/month)
- Need for real-time insights
- Time for server maintenance

### For Scale Phase:
**Professional analytics** (Google Analytics 4, Mixpanel, etc.) when you have:
- Large user base (>1000/month)
- Dedicated analytics team
- Complex tracking requirements
- Marketing/growth focus

## Current Status

### Why Dashboard Shows Zeros
1. **Analytics tracking was disabled** until recently (script was commented out)
2. **No historical data** exists yet
3. **Users need to interact** with the site for data to appear
4. **Data collection is cumulative** - it will build up over time

### Testing Analytics
```javascript
// In browser console, test analytics:
window.fairForwardAnalytics.getStoredEvents(); // See current events
window.fairForwardAnalytics.exportAnalyticsData(); // Download test data
```

### Sample Data for Testing
```bash
# Generate sample dashboard
python data_sources/analytics/collect_analytics.py --sample --output /tmp/sample.json
python data_sources/analytics/analytics_dashboard.py --input /tmp/sample.json --output /tmp/sample_dashboard.html
```

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