# Fair Forward Analytics System

## Overview
The analytics system tracks user interactions on the Fair Forward Data Catalog website and generates usage dashboards. It's designed to be privacy-focused, serverless, and fully automated.

## 🔄 How It Works: Complete Data Flow

### **What Gets Tracked**
- ✅ **Page visits**: When someone opens the website
- ✅ **Dataset card views**: When someone clicks on a dataset card  
- ✅ **Link clicks**: When someone opens dataset/model links
- ✅ **Search queries**: What people search for
- ✅ **Filter usage**: Which filters are most popular

### **The Complete Journey**

```
1. 👤 User visits Fair Forward website
   ↓
2. 📊 JavaScript automatically tracks interactions:
   • Page view recorded
   • Card clicks tracked  
   • Link clicks captured
   ↓
3. 🚀 After 5 events OR 30 seconds:
   • Data automatically sent to GitHub Issues API
   • No user action required!
   ↓
4. 📝 GitHub Issue created:
   Title: "Analytics Batch: 2024-01-15 (5 events)"
   Body: JSON data with all interactions
   ↓
5. ⏰ Daily at 6 AM UTC:
   • GitHub Action runs automatically
   • Reads all analytics issues
   • Extracts and aggregates data
   ↓
6. 📈 Dashboard generated:
   • Real usage statistics calculated
   • Beautiful HTML dashboard created
   • Automatically deployed to GitHub Pages
   ↓
7. 🎯 Result: Live dashboard shows real user engagement!
```

### **Why This Approach?**

**✅ Fully Automated**: No manual intervention needed  
**✅ Zero Cost**: Uses free GitHub features as database  
**✅ Privacy-First**: No external tracking services  
**✅ Reliable**: Built on GitHub's infrastructure  
**✅ Scalable**: Handles thousands of events  
**✅ Transparent**: All data visible in GitHub Issues  

## 🏗️ Technical Architecture

### **Frontend (Website)**
- **File**: `docs/umami-analytics.js`
- **Function**: Tracks user interactions in real-time
- **Storage**: Batches events and sends to GitHub Issues API
- **Privacy**: No cookies, no personal data collected

### **Backend (Serverless)**
- **Database**: GitHub Issues API (`jonas-nothnagel/fair-forward-analytics`)
- **Processing**: GitHub Actions workflow
- **Schedule**: Daily at 6 AM UTC
- **Output**: Static HTML dashboard

### **Data Flow Details**

#### 1. Event Collection (Browser)
```javascript
// Automatic tracking when user interacts with site
fairForwardAnalytics.trackPageView();
fairForwardAnalytics.trackCardView(card);
fairForwardAnalytics.trackLinkClick(link);
```

#### 2. Batch Sending (Automatic)
```javascript
// Every 5 events or 30 seconds, automatically:
POST https://api.github.com/repos/jonas-nothnagel/fair-forward-analytics/issues
{
  "title": "Analytics Batch: 2024-01-15 (5 events)",
  "body": "## Analytics Data\n```json\n[...events...]\n```",
  "labels": ["analytics", "automated"]
}
```

#### 3. Data Processing (GitHub Action)
```python
# Daily workflow:
1. Fetch all analytics issues from GitHub
2. Extract JSON data from issue bodies  
3. Aggregate events into statistics
4. Generate HTML dashboard
5. Deploy to GitHub Pages
```

## 📊 What You'll See

### **In Analytics Repository**
Issues like:
```
Title: Analytics Batch: 2024-01-15 (5 events)
Labels: analytics, automated

Body:
## Analytics Batch Report
**Session:** session_1705123456_abc123
**Total Events:** 5

### Event Summary
- page_view: 1
- card_view: 3  
- link_click: 1

### Detailed Events
```json
[...detailed event data...]
```
```

### **In Dashboard** 
Live statistics:
```
📊 Fair Forward Analytics Dashboard

📈 Usage Overview
• Total Page Views: 1,247
• Dataset Cards Viewed: 892
• External Links Clicked: 234
• Search Queries: 156

🔍 Popular Searches
• "climate data" (23 searches)
• "agriculture AI" (18 searches)
• "health datasets" (15 searches)

🌍 Most Viewed Datasets
• Climate Change Indicators (89 views)
• Agricultural AI Models (67 views)
• Health Data Commons (45 views)
```

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