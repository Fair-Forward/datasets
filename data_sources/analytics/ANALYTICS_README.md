# Fair Forward Analytics System

This document explains how to set up and use the analytics system for the Fair Forward Data Catalog.

## Overview

The analytics system provides privacy-focused tracking of user interactions with datasets and use cases. It's designed to be:

- **Open-source**: All code is available and customizable
- **Privacy-focused**: No personal data collection, GDPR compliant
- **Self-hosted**: Can run entirely on your infrastructure
- **Automated**: Integrates with your existing GitHub Actions workflow

## Features

### Tracked Events
- **Page Views**: Basic page visit tracking
- **Card Views**: When users click on dataset/use case cards
- **Link Clicks**: Clicks on dataset and use case links
- **Search Activity**: Search terms and frequency
- **Filter Usage**: Which filters are most popular
- **External Links**: Clicks on external resources

### Analytics Dashboard
- **Real-time Statistics**: Total events, sessions, views
- **Popular Content**: Most viewed projects, domains, data types
- **User Behavior**: Search patterns, filter preferences
- **Time-based Analysis**: Daily and hourly activity patterns
- **Visual Charts**: Interactive graphs using Chart.js

## Setup Options

### Option 1: Umami Analytics (Recommended)

[Umami](https://umami.is/) is an open-source, privacy-focused analytics platform.

#### Free Hosted Option:
1. Sign up at [umami.is](https://umami.is/)
2. Create a new website
3. Get your website ID and tracking script URL
4. Update `analytics_config.json`:
   ```json
   {
     "umami": {
       "enabled": true,
       "website_id": "your-website-id",
       "script_url": "https://analytics.umami.is/script.js"
     }
   }
   ```

#### Self-hosted Option:
1. Deploy Umami on your server (Docker/Vercel/Railway)
2. Follow the [Umami documentation](https://umami.is/docs)
3. Update configuration with your self-hosted URL

### Option 2: Local Analytics Only

For a completely self-contained solution:

1. Keep the default configuration
2. Analytics data will be stored locally in `analytics_data.json`
3. Dashboard will be generated from local data only

### Option 3: Custom Analytics Service

You can integrate with any analytics service by:

1. Modifying `docs/umami-analytics.js`
2. Updating the `sendToCustomEndpoint` method
3. Implementing your API endpoint

## Installation

1. **Copy the analytics files** to your repository:
   ```bash
   # Analytics tracking script
   cp umami-analytics.js docs/
   
   # Analytics collection and dashboard generation
   cp collect_analytics.py .
   cp analytics_dashboard.py .
   cp analytics_config.json .
   ```

2. **Update your HTML generation** (already done in `generate_catalog.py`):
   - Analytics script is included
   - Dashboard link is added to footer

3. **Set up the GitHub workflow**:
   - The workflow in `.github/workflows/analytics_update.yml` will run daily
   - It collects data and generates the dashboard automatically

## Configuration

Edit `analytics_config.json` to customize the analytics system:

```json
{
  "umami": {
    "enabled": false,           // Enable Umami integration
    "website_id": "your-id",    // Your Umami website ID
    "script_url": "..."         // Umami script URL
  },
  "tracking": {
    "track_clicks": true,       // Track card clicks
    "track_views": true,        // Track page views
    "track_filters": true,      // Track filter usage
    "track_searches": true      // Track search activity
  },
  "privacy": {
    "anonymize_ips": true,      // Anonymize IP addresses
    "respect_dnt": true,        // Respect Do Not Track
    "cookie_consent": false     // No cookies used
  }
}
```

## Usage

### Manual Dashboard Generation

Generate the analytics dashboard manually:

```bash
# Collect analytics data (with sample data for testing)
python collect_analytics.py --sample --dashboard

# Or generate dashboard from existing data
python analytics_dashboard.py --input analytics_data.json --output docs/analytics.html
```

### Automated Updates

The GitHub workflow automatically:
1. Runs daily at 6 AM UTC
2. Collects analytics data
3. Generates updated dashboard
4. Commits changes to the repository

### Viewing Analytics

- **Dashboard**: Visit `https://your-site.github.io/analytics.html`
- **Raw Data**: Check `analytics_data.json` for raw event data

## Privacy & Compliance

### GDPR Compliance
- No personal data is collected
- No cookies are used
- IP addresses can be anonymized
- Users can opt-out via Do Not Track

### Data Retention
- Local data is kept for 365 days by default
- Configure retention in `analytics_config.json`
- Data is automatically cleaned up

### Transparency
- All tracking code is open-source
- Users can inspect what data is collected
- Clear privacy policy can be added

## Customization

### Adding New Event Types

1. **Frontend**: Add tracking in `docs/umami-analytics.js`:
   ```javascript
   trackCustomEvent(eventName, eventData) {
       this.sendEvent(eventName, eventData);
   }
   ```

2. **Backend**: Update `analytics_dashboard.py` to process new events:
   ```python
   elif event_name == 'custom_event':
       # Process your custom event
       pass
   ```

### Custom Dashboard Widgets

Modify `analytics_dashboard.py` to add new visualizations:

```python
def generate_custom_chart(stats):
    # Add your custom chart logic
    return chart_html
```

### Integration with Other Services

You can send data to multiple analytics services simultaneously by updating the `sendEvent` method in `umami-analytics.js`.

## Troubleshooting

### Common Issues

1. **No data in dashboard**:
   - Check if analytics script is loaded
   - Verify configuration in `analytics_config.json`
   - Run with `--sample` flag for testing

2. **Dashboard not updating**:
   - Check GitHub Actions logs
   - Verify workflow permissions
   - Run manual collection

3. **Umami integration not working**:
   - Verify website ID and script URL
   - Check browser console for errors
   - Test with Umami's debug mode

### Debug Mode

Enable debug mode in the analytics script:

```javascript
const analyticsConfig = {
    debug: true,  // Set to true for debugging
    // ... other config
};
```

This will log all events to the browser console.

## Comparison with Google Analytics

| Feature | Fair Forward Analytics | Google Analytics 4 |
|---------|----------------------|-------------------|
| **Privacy** | ✅ No personal data | ❌ Collects personal data |
| **Open Source** | ✅ Fully open | ❌ Proprietary |
| **Self-hosted** | ✅ Optional | ❌ Google-hosted only |
| **GDPR Compliant** | ✅ By design | ⚠️ Requires configuration |
| **No Cookies** | ✅ Cookie-free | ❌ Uses cookies |
| **Cost** | ✅ Free forever | ✅ Free tier available |
| **Setup Complexity** | ⚠️ Moderate | ✅ Simple |
| **Advanced Features** | ⚠️ Basic | ✅ Advanced |

## Future Enhancements

Potential improvements to consider:

1. **Real-time Dashboard**: WebSocket-based live updates
2. **A/B Testing**: Built-in experiment tracking
3. **Heatmaps**: Visual interaction tracking
4. **API Integration**: RESTful API for external access
5. **Mobile Analytics**: Enhanced mobile tracking
6. **Performance Metrics**: Page load time tracking

## Support

For questions or issues:

1. **Technical Issues**: Open an issue on GitHub
2. **Feature Requests**: Submit a feature request
3. **Configuration Help**: Check this documentation
4. **Privacy Questions**: Review the privacy section

## License

This analytics system is released under the same license as the main project. All code is open-source and can be freely modified and distributed. 