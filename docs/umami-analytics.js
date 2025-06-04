/**
 * Custom Analytics Tracking for Fair Forward Data Catalog
 * This script tracks user interactions with datasets and use cases
 * Compatible with Umami Analytics and other privacy-focused solutions
 */

class FairForwardAnalytics {
    constructor(config = {}) {
        this.config = {
            githubRepo: null,
            githubToken: null,
            trackClicks: true,
            trackViews: true,
            trackFilters: true,
            trackDownloads: true,
            batchSize: 5,
            batchTimeout: 30000,
            debug: false,
            ...config
        };
        
        this.sessionId = this.generateSessionId();
        this.eventQueue = [];
        this.batchTimer = null;
        
        this.init();
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        if (this.config.trackViews) {
            this.trackPageView();
        }
        
        if (this.config.trackClicks) {
            this.setupEventListeners();
        }
        
        // Start batch processing
        this.startBatchTimer();
        
        if (this.config.debug) {
            console.log('Fair Forward Analytics initialized', this.config);
        }
    }
    
    setupEventListeners() {
        // Track card clicks (dataset/use case views)
        document.addEventListener('click', (e) => {
            // Track detail panel opens
            if (e.target.closest('.details-link') || e.target.closest('.card-description') || e.target.closest('.card-footer')) {
                const card = e.target.closest('.card');
                if (card) {
                    this.trackCardView(card);
                }
            }
            
            // Track dataset/use case link clicks
            if (e.target.closest('.hidden-link')) {
                const link = e.target.closest('.hidden-link');
                this.trackLinkClick(link);
            }
            
            // Track filter usage
            if (e.target.matches('select') || e.target.closest('.search-box')) {
                setTimeout(() => this.trackFilterUsage(), 100);
            }
            
            // Track external links
            if (e.target.closest('a[href^="http"]')) {
                const link = e.target.closest('a');
                this.trackExternalLink(link);
            }
        });
        
        // Track search input
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (searchInput.value.length > 2) {
                        this.trackSearch(searchInput.value);
                    }
                }, 500);
            });
        }
        
        // Track filter changes
        ['viewFilter', 'domainFilter', 'dataTypeFilter', 'regionFilter'].forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                filter.addEventListener('change', () => {
                    this.trackFilterChange(filterId, filter.value);
                });
            }
        });
    }
    
    trackPageView() {
        this.sendEvent('page_view', {
            url: window.location.pathname + window.location.search,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            timestamp: new Date().toISOString()
        });
    }
    
    trackCardView(card) {
        const projectId = card.getAttribute('data-project-id');
        const title = card.getAttribute('data-title');
        const region = card.getAttribute('data-region');
        const hasDataset = card.classList.contains('has-dataset');
        const hasUsecase = card.classList.contains('has-usecase');
        
        // Get domain tags
        const domainTags = Array.from(card.querySelectorAll('.domain-badge')).map(badge => badge.textContent);
        
        // Get data types
        const dataTypes = Array.from(card.querySelectorAll('.data-type-chip')).map(chip => 
            chip.getAttribute('data-filter') || chip.textContent.trim()
        );
        
        this.sendEvent('card_view', {
            project_id: projectId,
            title: title,
            region: region,
            domains: domainTags,
            data_types: dataTypes,
            has_dataset: hasDataset,
            has_usecase: hasUsecase,
            timestamp: new Date().toISOString()
        });
        
        if (this.config.debug) {
            console.log('Card view tracked:', { projectId, title, region, domainTags, dataTypes });
        }
    }
    
    trackLinkClick(link) {
        const linkType = link.getAttribute('data-link-type');
        const linkName = link.getAttribute('data-link-name');
        const href = link.getAttribute('href');
        const card = link.closest('.card');
        const projectId = card ? card.getAttribute('data-project-id') : null;
        
        this.sendEvent('link_click', {
            link_type: linkType,
            link_name: linkName,
            href: href,
            project_id: projectId,
            timestamp: new Date().toISOString()
        });
        
        if (this.config.debug) {
            console.log('Link click tracked:', { linkType, linkName, href, projectId });
        }
    }
    
    trackFilterChange(filterId, value) {
        this.sendEvent('filter_change', {
            filter_type: filterId,
            filter_value: value,
            timestamp: new Date().toISOString()
        });
        
        if (this.config.debug) {
            console.log('Filter change tracked:', { filterId, value });
        }
    }
    
    trackSearch(searchTerm) {
        this.sendEvent('search', {
            search_term: searchTerm,
            timestamp: new Date().toISOString()
        });
        
        if (this.config.debug) {
            console.log('Search tracked:', searchTerm);
        }
    }
    
    trackExternalLink(link) {
        const href = link.getAttribute('href');
        const text = link.textContent.trim();
        
        this.sendEvent('external_link_click', {
            href: href,
            link_text: text,
            timestamp: new Date().toISOString()
        });
        
        if (this.config.debug) {
            console.log('External link tracked:', { href, text });
        }
    }
    
    trackFilterUsage() {
        const activeFilters = {};
        
        ['viewFilter', 'domainFilter', 'dataTypeFilter', 'regionFilter'].forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter && filter.value !== 'all') {
                activeFilters[filterId] = filter.value;
            }
        });
        
        const searchInput = document.getElementById('searchInput');
        if (searchInput && searchInput.value) {
            activeFilters.search = searchInput.value;
        }
        
        if (Object.keys(activeFilters).length > 0) {
            this.sendEvent('filter_usage', {
                active_filters: activeFilters,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    sendEvent(eventName, eventData) {
        // Add to event queue for batch processing
        this.addToQueue(eventName, eventData);
        
        // Store locally as backup
        this.storeEventLocally(eventName, eventData);
        
        if (this.config.debug) {
            console.log('Event queued:', eventName, eventData);
        }
    }
    
    addToQueue(eventName, eventData) {
        const event = {
            event_name: eventName,
            event_data: eventData,
            timestamp: new Date().toISOString(),
            session_id: this.sessionId,
            url: window.location.href,
            user_agent: navigator.userAgent.substring(0, 100) // Truncated for privacy
        };
        
        this.eventQueue.push(event);
        
        // Send batch if queue is full
        if (this.eventQueue.length >= this.config.batchSize) {
            this.sendBatchNow();
        }
    }
    
    sendBatchNow() {
        if (this.eventQueue.length === 0) return;
        
        const batch = [...this.eventQueue];
        this.eventQueue = []; // Clear queue
        
        this.sendBatch(batch);
    }
    
    // Method to send batch to GitHub Issues API
    async sendBatch(events) {
        if (!this.config.githubRepo || events.length === 0) {
            if (this.config.debug) {
                console.log('Skipping batch send - no repo configured or no events');
            }
            return;
        }
        
        try {
            // Create a summary of the batch
            const summary = this.createBatchSummary(events);
            
            // Send to GitHub Issues API (public endpoint, no auth needed)
            const response = await fetch(`https://api.github.com/repos/${this.config.githubRepo}/issues`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.github.v3+json'
                },
                body: JSON.stringify({
                    title: `Analytics Batch: ${summary.date} (${events.length} events)`,
                    body: this.formatBatchForIssue(events, summary),
                    labels: ['analytics', 'automated', `session-${this.sessionId.split('_')[1]}`]
                })
            });
            
            if (response.ok) {
                if (this.config.debug) {
                    console.log('Analytics batch sent successfully:', events.length, 'events');
                }
                // Clear localStorage backup since data was sent successfully
                this.clearStoredEvents();
            } else {
                throw new Error(`GitHub API responded with ${response.status}`);
            }
        } catch (error) {
            if (this.config.debug) {
                console.error('Failed to send analytics batch:', error);
            }
            // Keep events in localStorage as backup
        }
    }
    
    createBatchSummary(events) {
        const eventTypes = {};
        events.forEach(event => {
            eventTypes[event.event_name] = (eventTypes[event.event_name] || 0) + 1;
        });
        
        return {
            date: new Date().toISOString().split('T')[0],
            time: new Date().toISOString(),
            total_events: events.length,
            event_types: eventTypes,
            session_id: this.sessionId,
            url: window.location.href
        };
    }
    
    formatBatchForIssue(events, summary) {
        return `## Analytics Batch Report

**Session:** ${summary.session_id}
**Date:** ${summary.date}
**URL:** ${summary.url}
**Total Events:** ${summary.total_events}

### Event Summary
${Object.entries(summary.event_types).map(([type, count]) => `- ${type}: ${count}`).join('\n')}

### Detailed Events
\`\`\`json
${JSON.stringify(events, null, 2)}
\`\`\`

---
*Automated analytics collection for Fair Forward Data Catalog*`;
    }
    
    storeEventLocally(eventName, eventData) {
        try {
            const events = JSON.parse(localStorage.getItem('ff_analytics_events') || '[]');
            events.push({
                event_name: eventName,
                event_data: eventData,
                timestamp: new Date().toISOString(),
                session_id: this.sessionId
            });
            
            // Keep only last 100 events to prevent storage bloat
            if (events.length > 100) {
                events.splice(0, events.length - 100);
            }
            
            localStorage.setItem('ff_analytics_events', JSON.stringify(events));
        } catch (error) {
            if (this.config.debug) {
                console.error('Failed to store event locally:', error);
            }
        }
    }
    
    // Method to get locally stored events (useful for debugging or batch sending)
    getStoredEvents() {
        try {
            return JSON.parse(localStorage.getItem('ff_analytics_events') || '[]');
        } catch (error) {
            return [];
        }
    }
    
    // Method to export analytics data for sharing
    exportAnalyticsData() {
        const events = this.getStoredEvents();
        if (events.length === 0) {
            alert('No analytics data to export yet. Browse some datasets first!');
            return null;
        }
        
        const exportData = {
            export_timestamp: new Date().toISOString(),
            session_count: 1, // This session
            total_events: events.length,
            events: events
        };
        
        // Create downloadable file
        const blob = new Blob([JSON.stringify(exportData, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ff_analytics_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        return exportData;
    }
    
    // Add a small analytics sharing prompt
    addAnalyticsPrompt() {
        // Only show after user has some activity
        setTimeout(() => {
            const events = this.getStoredEvents();
            if (events.length >= 5 && !localStorage.getItem('ff_analytics_prompt_shown')) {
                const shouldShow = confirm(
                    'Help improve Fair Forward! 📊\n\n' +
                    'You\'ve browsed several datasets. Would you like to share your anonymous usage data to help us improve the catalog?\n\n' +
                    'This will download a file you can optionally send to us. No personal data is included.'
                );
                
                if (shouldShow) {
                    this.exportAnalyticsData();
                }
                
                localStorage.setItem('ff_analytics_prompt_shown', 'true');
            }
        }, 30000); // Show after 30 seconds of activity
    }

    // Method to clear stored events
    clearStoredEvents() {
        localStorage.removeItem('ff_analytics_events');
    }

    // Method to start batch processing
    startBatchTimer() {
        if (this.batchTimer) {
            clearTimeout(this.batchTimer);
        }
        this.batchTimer = setTimeout(() => {
            this.processBatch();
        }, this.config.batchTimeout);
    }

    // Method to process batch
    processBatch() {
        const events = this.getStoredEvents();
        if (events.length > 0) {
            this.sendBatch(events);
        }
        this.startBatchTimer();
    }
}

// Initialize analytics when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Configuration - you can modify these values
    const analyticsConfig = {
        // GitHub Analytics Backend (serverless)
        githubRepo: 'jonas-nothnagel/fair-forward-analytics', // Repository for analytics data
        githubToken: null, // Will be set via environment or public collection
        
        // Tracking options
        trackClicks: true,
        trackViews: true,
        trackFilters: true,
        trackDownloads: true,
        
        // Batch settings
        batchSize: 5, // Send events in batches of 5
        batchTimeout: 30000, // Send batch after 30 seconds
        
        // Debug mode (set to false in production)
        debug: false,
        
        // Prompt option
        prompt: false // Disabled since we're auto-collecting
    };
    
    // Initialize analytics
    window.fairForwardAnalytics = new FairForwardAnalytics(analyticsConfig);
    
    // Add optional analytics sharing prompt (can be disabled by setting prompt: false in config)
    if (analyticsConfig.prompt !== false) {
        window.fairForwardAnalytics.addAnalyticsPrompt();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FairForwardAnalytics;
} 