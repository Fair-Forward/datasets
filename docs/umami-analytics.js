/**
 * Custom Analytics Tracking for Fair Forward Data Catalog
 * This script tracks user interactions with datasets and use cases
 * Compatible with Umami Analytics and other privacy-focused solutions
 */

class FairForwardAnalytics {
    constructor(config = {}) {
        this.config = {
            // Umami configuration
            websiteId: config.websiteId || null,
            apiEndpoint: config.apiEndpoint || 'https://analytics.umami.is/api/send',
            
            // Custom tracking configuration
            trackClicks: config.trackClicks !== false,
            trackViews: config.trackViews !== false,
            trackFilters: config.trackFilters !== false,
            trackDownloads: config.trackDownloads !== false,
            
            // Debug mode (set to false in production)
            debug: true
        };
        
        this.sessionId = this.generateSessionId();
        this.init();
    }
    
    generateSessionId() {
        return 'ff_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        if (this.config.debug) {
            console.log('Fair Forward Analytics initialized', this.config);
        }
        
        // Track page view
        this.trackPageView();
        
        // Set up event listeners
        this.setupEventListeners();
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
        // Send to Umami if configured
        if (this.config.websiteId && window.umami) {
            window.umami.track(eventName, eventData);
        }
        
        // Send to custom endpoint if configured
        if (this.config.apiEndpoint && this.config.websiteId) {
            this.sendToCustomEndpoint(eventName, eventData);
        }
        
        // Store locally for potential batch sending
        this.storeEventLocally(eventName, eventData);
        
        if (this.config.debug) {
            console.log('Event sent:', eventName, eventData);
        }
    }
    
    sendToCustomEndpoint(eventName, eventData) {
        const payload = {
            website_id: this.config.websiteId,
            session_id: this.sessionId,
            event_name: eventName,
            event_data: eventData,
            url: window.location.href,
            timestamp: new Date().toISOString()
        };
        
        // Use sendBeacon for reliability, fallback to fetch
        if (navigator.sendBeacon) {
            navigator.sendBeacon(this.config.apiEndpoint, JSON.stringify(payload));
        } else {
            fetch(this.config.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
                keepalive: true
            }).catch(error => {
                if (this.config.debug) {
                    console.error('Failed to send analytics event:', error);
                }
            });
        }
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
    
    // Method to clear stored events
    clearStoredEvents() {
        localStorage.removeItem('ff_analytics_events');
    }
}

// Initialize analytics when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Configuration - you can modify these values
    const analyticsConfig = {
        // Umami configuration (set these when you have Umami set up)
        websiteId: null, // Set this to your Umami website ID
        apiEndpoint: null, // Set this to your Umami API endpoint
        
        // Tracking options
        trackClicks: true,
        trackViews: true,
        trackFilters: true,
        trackDownloads: true,
        
        // Debug mode (set to false in production)
        debug: true
    };
    
    // Initialize analytics
    window.fairForwardAnalytics = new FairForwardAnalytics(analyticsConfig);
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FairForwardAnalytics;
} 