/**
 * Enhanced Side Panel Implementation
 * This file contains the improved side panel functionality for the data catalog
 */

// Enhanced markdown parser
function parseMarkdown(markdown) {
    if (!markdown) return '';
    
    // Remove the first h1 header if it exists
    markdown = markdown.replace(/^# .*$/m, '').trim();
    
    // Replace headers
    let html = markdown
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Replace links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" class="panel-link"><i class="fas fa-arrow-up-right-from-square"></i> $1</a>');
    
    // Replace images
    html = html.replace(/!\[([^\]]+)\]\(([^)]+)\)/gim, '<div class="panel-image-container"><img src="$2" alt="$1" class="panel-image"><div class="panel-image-caption">$1</div></div>');
    
    // Replace bold text
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    
    // Replace italic text
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
    
    // Replace code blocks with syntax highlighting wrapper
    html = html.replace(/```([^`\n]*)\n([^`]+)```/gim, function(match, language, code) {
        return `<div class="code-block-wrapper">
            <div class="code-block-header">
                <span class="code-language">${language || 'code'}</span>
                <button class="copy-code-btn" onclick="copyToClipboard(this)">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
            <pre class="code-block"><code class="language-${language || 'plaintext'}">${code.trim()}</code></pre>
        </div>`;
    });
    
    // Replace inline code
    html = html.replace(/`([^`]+)`/gim, '<code class="inline-code">$1</code>');
    
    // Replace bullet lists with better formatting
    // First, identify bullet points with proper indentation
    let bulletListPattern = /^\s*[\*\-]\s+(.*?)$/gim;
    let bulletMatches = [...html.matchAll(bulletListPattern)];
    
    if (bulletMatches.length > 0) {
        // Process bullet points with proper HTML structure
        let inList = false;
        let listItems = [];
        
        // Split by lines to process each line
        let lines = html.split('\n');
        let newLines = [];
        
        for (let line of lines) {
            let bulletMatch = line.match(bulletListPattern);
            
            if (bulletMatch) {
                if (!inList) {
                    // Start a new list
                    newLines.push('<ul class="panel-list">');
                    inList = true;
                }
                // Add list item with enhanced styling
                newLines.push(`<li class="panel-list-item">${bulletMatch[1]}</li>`);
            } else {
                if (inList) {
                    // Close the list
                    newLines.push('</ul>');
                    inList = false;
                }
                newLines.push(line);
            }
        }
        
        // Close any open list
        if (inList) {
            newLines.push('</ul>');
        }
        
        html = newLines.join('\n');
    }
    
    // Replace paragraphs (must be done last)
    html = html.replace(/^(?!<[a-z])(.*$)/gim, '<p>$1</p>');
    
    // Fix nested lists and paragraphs
    html = html.replace(/<\/ul>\s*<ul>/gim, '');
    html = html.replace(/<\/p>\s*<p>/gim, '</p><p>');
    
    // Fix empty paragraphs
    html = html.replace(/<p>\s*<\/p>/gim, '');
    
    return html;
}

// Function to copy code to clipboard
function copyToClipboard(button) {
    const codeBlock = button.closest('.code-block-wrapper').querySelector('code');
    const textToCopy = codeBlock.textContent;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Change button icon temporarily
        const icon = button.querySelector('i');
        icon.className = 'fas fa-check';
        
        setTimeout(() => {
            icon.className = 'fas fa-copy';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

// Enhanced function to load item details
function loadItemDetails(itemId) {
    const card = document.querySelector(`.card[data-id="${itemId}"]`);
    if (!card) return;
    
    const title = card.getAttribute('data-title');
    const tags = Array.from(card.querySelectorAll('.tag')).map(tag => tag.textContent);
    const region = card.getAttribute('data-region');
    const projectId = card.getAttribute('data-project-id');
    
    // --- START: Extract Authors and Orgs from Data Attributes ---
    const authorsContentHTML = card.getAttribute('data-authors');
    const organizationsContentHTML = card.getAttribute('data-organizations');
    console.log('Authors data:', authorsContentHTML);
    console.log('Organizations data:', organizationsContentHTML);
    // --- END: Extract Authors and Orgs from Data Attributes ---
    
    // --- START: Extract multiple Dataset and Use Case links ---
    const datasetLinkElements = card.querySelectorAll('.hidden-links .hidden-link[data-link-type="dataset"]');
    const useCaseLinkElements = card.querySelectorAll('.hidden-links .hidden-link[data-link-type="usecase"]');
    
    const datasetLinks = Array.from(datasetLinkElements).map(el => ({
        href: el.getAttribute('href'),
        name: el.getAttribute('data-link-name') || el.textContent.replace('View ', '').trim() || 'Dataset Link'
    }));
    const useCaseLinks = Array.from(useCaseLinkElements).map(el => ({
        href: el.getAttribute('href'),
        name: el.getAttribute('data-link-name') || el.textContent.replace('View ', '').trim() || 'Use Case Link'
    }));
    console.log('Dataset links for panel:', datasetLinks);
    console.log('Use Case links for panel:', useCaseLinks);
    // --- END: Extract multiple Dataset and Use Case links ---
    
    // Basic check if projectId exists
    if (!projectId) {
        console.error('Could not find project ID for card with data-id:', itemId);
        // Optionally display an error in the panel
        const detailPanelLoader = document.getElementById('detailPanelLoader');
        const detailPanelData = document.getElementById('detailPanelData');
        if (detailPanelLoader) detailPanelLoader.style.display = 'none';
        if (detailPanelData) {
             detailPanelData.innerHTML = '<p>Error: Could not load project details (missing project ID).</p>';
             detailPanelData.style.display = 'block';
        }
        return;
    }
    console.log('Project ID for fetching docs:', projectId);
    
    // Get additional card information
    const cardImage = card.querySelector('.card-image');
    const hasImage = cardImage && cardImage.classList.contains('has-image');
    
    // Improved image style extraction
    let imageStyle = null;
    if (hasImage && cardImage) {
        // Get the full style attribute
        imageStyle = cardImage.getAttribute('style');
        console.log('Image style found:', imageStyle);
        
        // If style doesn't contain background-image, try to extract it differently
        if (!imageStyle || !imageStyle.includes('background-image')) {
            const computedStyle = window.getComputedStyle(cardImage);
            const backgroundImage = computedStyle.getPropertyValue('background-image');
            if (backgroundImage && backgroundImage !== 'none') {
                imageStyle = `background-image: ${backgroundImage};`;
                console.log('Computed image style:', imageStyle);
            }
        }
    }
    
    // Function to get icon for data type based on normalized class
    const getDataTypeIcon = (normalized) => {
        if (!normalized) return 'fa-database';
        
        const iconMap = {
            'images': 'fa-images',
            'image': 'fa-images',
            'drone-imagery': 'fa-satellite',
            'audio': 'fa-microphone',
            'text': 'fa-file-lines',
            'geospatial': 'fa-earth-americas',
            'geospatialremote-sensing': 'fa-earth-americas',
            'geospatial-remote-sensing': 'fa-earth-americas',
            'tabular': 'fa-table-cells',
            'video': 'fa-film',
            'voice': 'fa-microphone-lines',
            'meterological': 'fa-cloud-sun',
            'meteorological': 'fa-cloud-sun'
        };
        
        // Check if normalized starts with any key
        for (const [key, icon] of Object.entries(iconMap)) {
            if (normalized === key || normalized.startsWith(key)) {
                return icon;
            }
        }
        
        return 'fa-database'; // default
    };
    
    // Get data type chips
    const dataTypeChips = Array.from(card.querySelectorAll('.data-type-chip')).map(chip => {
        const chipClass = Array.from(chip.classList).find(c => c.startsWith('label-'));
        console.log('Data type chip class:', chipClass, 'from', chip.classList);
        
        // Get normalized class name (remove 'label-' prefix)
        const normalized = chipClass ? chipClass.replace('label-', '') : '';
        
        // Get icon based on normalized class
        const iconClass = getDataTypeIcon(normalized);
        
        // Get text content
        const chipText = chip.textContent.trim();
        
        return {
            text: chipText,
            iconClass: iconClass,
            class: chipClass,
            filter: chip.getAttribute('data-filter')
        };
    });
    
    // Get domain badges and separate SDG badges
    const allDomainBadges = Array.from(card.querySelectorAll('.domain-badge')).map(badge => {
        const badgeClass = Array.from(badge.classList).find(c => c.startsWith('domain-'));
        console.log('Domain badge class:', badgeClass, 'from', badge.classList);
        return {
            text: badge.textContent.trim(),
            class: badgeClass
        };
    });
    
    // Separate SDG badges from other domain badges
    const sdgBadges = [];
    const domainBadges = [];
    
    allDomainBadges.forEach(badge => {
        const sdgMatch = badge.text.match(/SDG\s*(\d+)/i);
        if (sdgMatch) {
            const sdgNum = parseInt(sdgMatch[1]);
            if (sdgNum >= 1 && sdgNum <= 17) {
                sdgBadges.push(sdgNum);
            }
        } else {
            domainBadges.push(badge);
        }
    });
    
    // Remove duplicates from SDG badges
    const uniqueSdgBadges = [...new Set(sdgBadges)].sort((a, b) => a - b);
    
    // Show loading state
    const detailPanelLoader = document.getElementById('detailPanelLoader');
    const detailPanelData = document.getElementById('detailPanelData');
    
    if (detailPanelLoader && detailPanelData) {
        detailPanelLoader.style.display = 'flex';
        detailPanelData.style.display = 'none';
    }
    
    // Initialize content sections
    let contentSections = {
        'What is this about?': '',
        'Data Characteristics': '',
        'Model Characteristics': '',
        'How to Use It': ''
    };
    
    // Create a counter to track when all fetches are complete
    let fetchesCompleted = 0;
    let totalFetches = 0;
    
    // Function to update the UI when all fetches are complete
    function updateDetailPanel() {
        console.log('Updating panel with sections:', contentSections);
        let detailContent = '';
        
        // Add header image if available
        if (hasImage && imageStyle) {
            detailContent += `<div class="panel-header-image" style="${imageStyle}"></div>`;
        }
        
        // Add domain badges and title section
        detailContent += `<div class="panel-title-section">`;
        
        // Add domain badges
        if (domainBadges.length > 0) {
            detailContent += `<div class="panel-domain-badges">`;
            domainBadges.forEach(badge => {
                // Log the badge object to see what we're working with
                console.log('Badge object:', badge);
                
                // Extract the domain name from the badge text and normalize it for use as a class
                const domainText = badge.text.trim();
                const domainClass = 'domain-' + domainText.toLowerCase().replace(/\s+/g, '-');
                
                // Create the badge HTML with the domain-specific class
                const badgeHTML = `<div class="panel-domain-badge ${domainClass}">${domainText}</div>`;
                console.log('Generated domain badge HTML:', badgeHTML);
                detailContent += badgeHTML;
            });
            detailContent += `</div>`;
        }
        
        // Add links section
        detailContent += `<div class="panel-links-section">`;
        // --- START: Add multiple Dataset links/buttons ---
        if (datasetLinks.length > 0) {
            datasetLinks.forEach(link => {
                detailContent += `<a href="${link.href}" target="_blank" class="panel-link-btn panel-dataset-link">
                    <i class="fas fa-cloud-arrow-down"></i> ${link.name}
                </a>`;
            });
        }
        // --- END: Add multiple Dataset links/buttons ---
        
        // --- START: Add multiple Use Case links/buttons ---
        if (useCaseLinks.length > 0) {
            useCaseLinks.forEach(link => {
                detailContent += `<a href="${link.href}" target="_blank" class="panel-link-btn panel-usecase-link">
                    <i class="fas fa-sparkles"></i> ${link.name}
                </a>`;
            });
        }
        // --- END: Add multiple Use Case links/buttons ---
        detailContent += `</div>`; // Close panel-links-section
        
        detailContent += `</div>`; // Close panel-title-section
        
        // Create a table of contents if we have multiple sections
        let hasMultipleSections = Object.values(contentSections).filter(Boolean).length > 1;
        
        if (hasMultipleSections) {
            let tocContent = '<div class="panel-toc">';
            tocContent += '<div class="panel-toc-title"><i class="fas fa-list"></i> Contents</div>';
            tocContent += '<ul class="panel-toc-list">';
            
            // Add TOC items for each main documentation section with content
            for (const [section, content] of Object.entries(contentSections)) {
                if (content) {
                    const sectionId = section.toLowerCase().replace(/\s+/g, '-');
                    let icon = 'fa-file-lines';
                    if (section.includes('Data')) icon = 'fa-database';
                    else if (section.includes('Model')) icon = 'fa-robot';
                    else if (section.includes('How to Use')) icon = 'fa-lightbulb';
                    else if (section === 'What is this about?') icon = 'fa-circle-info';
                    
                    tocContent += `<li class="panel-toc-item">
                        <a href="#${sectionId}" class="panel-toc-link">
                            <i class="fas ${icon}"></i> ${section}
                        </a>
                    </li>`;
                }
            }
            
            // Add TOC item for Organizations if it exists
            if (organizationsContentHTML) {
                 tocContent += `<li class="panel-toc-item">
                    <a href="#organizations" class="panel-toc-link">
                        <i class="fas fa-building"></i> Organizations Involved
                    </a>
                </li>`;
            }
            
            tocContent += '</ul></div>';
            detailContent += tocContent;
        }
        
        // Add each section that has content
        for (const [section, content] of Object.entries(contentSections)) {
            if (content) {
                const sectionId = section.toLowerCase().replace(/\s+/g, '-');
                
                // Special handling for "What is this about?" section - add SDG icons
                if (section === 'What is this about?' && uniqueSdgBadges.length > 0) {
                    let sdgIconsHTML = '<div class="sdg-icons-container">';
                    uniqueSdgBadges.forEach(sdgNum => {
                        sdgIconsHTML += `
                            <img src="./img/sdg-${sdgNum}.png" 
                                 alt="SDG ${sdgNum}" 
                                 class="sdg-icon"
                                 onerror="this.style.display='none'">
                        `;
                    });
                    sdgIconsHTML += '</div>';
                    
                    detailContent += `
                        <div class="detail-section" id="${sectionId}">
                            <h3 data-section="${section}">${section}</h3>
                            <div class="documentation-content">${content}</div>
                            ${sdgIconsHTML}
                        </div>
                    `;
                }
                // Special handling for Data Characteristics section - add data type chips
                else if (section === 'Data Characteristics' && dataTypeChips.length > 0) {
                    let dataTypesHTML = '<div class="data-types-container">';
                    dataTypeChips.forEach(chip => {
                        const iconClass = chip.iconClass || 'fa-database';
                        const chipText = chip.text;
                        dataTypesHTML += `
                            <div class="data-type-item ${chip.class || ''}">
                                <div class="data-type-header">
                                    <i class="fas ${iconClass}"></i>
                                    <span class="data-type-label">${chipText}</span>
                                </div>
                            </div>
                        `;
                    });
                    dataTypesHTML += '</div>';
                    
                    detailContent += `
                        <div class="detail-section" id="${sectionId}">
                            <h3 data-section="${section}">${section}</h3>
                            ${dataTypesHTML}
                            <div class="documentation-content">${content}</div>
                        </div>
                    `;
                } else {
                    detailContent += `
                        <div class="detail-section" id="${sectionId}">
                            <h3 data-section="${section}">${section}</h3>
                            <div class="documentation-content">${content}</div>
                        </div>
                    `;
                }
            }
        }
        
        // --- Reorder sections: Orgs -> Region -> Authors -> Tags ---
        
        // Add Organizations Section
        if (organizationsContentHTML) {
            // Parse organizations into three categories, preserving HTML
            const extractOrgSection = (label) => {
                const labelPattern = new RegExp(`${label}:\\s*`, 'i');
                const labelIndex = organizationsContentHTML.search(labelPattern);
                if (labelIndex === -1) return null;
                
                const startIndex = labelIndex + organizationsContentHTML.substring(labelIndex).indexOf(':') + 1;
                const remainingText = organizationsContentHTML.substring(startIndex);
                
                // Find the next label or end of string
                const nextLabels = [
                    remainingText.search(/Catalyzed by:/i),
                    remainingText.search(/Financed by:/i),
                    remainingText.search(/Powered by:/i)
                ].filter(idx => idx >= 0);
                
                const endIndex = nextLabels.length > 0 ? Math.min(...nextLabels) : remainingText.length;
                return remainingText.substring(0, endIndex).trim();
            };
            
            const poweredBy = extractOrgSection('Powered by');
            const catalyzedBy = extractOrgSection('Catalyzed by');
            const financedBy = extractOrgSection('Financed by');
            
            detailContent += `
                <div class="detail-section" id="organizations">
                    <h3 data-section="Organizations Involved">Organizations Involved</h3>
                    <div class="organizations-container">
                        ${poweredBy ? `
                            <div class="org-type org-powered">
                                <div class="org-type-header">
                                    <i class="fas fa-rocket"></i>
                                    <span class="org-type-label">Powered by</span>
                                </div>
                                <div class="org-type-content">${poweredBy}</div>
                            </div>
                        ` : ''}
                        ${catalyzedBy ? `
                            <div class="org-type org-catalyzed">
                                <div class="org-type-header">
                                    <i class="fas fa-seedling"></i>
                                    <span class="org-type-label">Catalyzed by</span>
                                </div>
                                <div class="org-type-content">${catalyzedBy}</div>
                            </div>
                        ` : ''}
                        ${financedBy ? `
                            <div class="org-type org-financed">
                                <div class="org-type-header">
                                    <i class="fas fa-coins"></i>
                                    <span class="org-type-label">Financed by</span>
                                </div>
                                <div class="org-type-content">${financedBy}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        // Add region section if available
        if (region) {
            detailContent += `
                <div class="detail-section" id="region">
                    <h3 data-section="Region">Region</h3>
                    <div class="documentation-content">
                        <p><i class="fas fa-location-dot"></i> ${region}</p>
                    </div>
                </div>
            `;
        }
        
        // Add Authors Section
        if (authorsContentHTML) {
            detailContent += `
                <div class="detail-section" id="authors">
                    <h3 data-section="Authors">Authors</h3>
                    <div class="documentation-content">
                        ${authorsContentHTML} 
                    </div>
                </div>
            `;
        }

        // Add tags section LAST
        if (tags && tags.length > 0) {
            detailContent += `
                <div class="detail-section" id="tags">
                    <h3 data-section="Tags">Tags</h3>
                    <div class="documentation-content">
                        <div class="tags">
                            ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        // --- End Reordering ---
        
        // Update the detail panel content
        const detailPanelData = document.getElementById('detailPanelData');
        const detailPanelLoader = document.getElementById('detailPanelLoader');
        
        if (detailPanelData && detailPanelLoader) {
            detailPanelData.innerHTML = detailContent;
            detailPanelLoader.style.display = 'none';
            detailPanelData.classList.add('active');
            detailPanelData.style.display = 'block';
        } else {
            console.error('Could not find detail panel elements');
        }
    }
    
    // Function to try loading a file from multiple possible directories
    async function tryLoadFile(fileName, section) {
        // Use the projectId obtained earlier
        const path = `./public/projects/${projectId}/docs/${fileName}`;
        console.log('Trying to load from:', path);
        try {
            const response = await fetch(path);
            if (response.ok) {
                const content = await response.text();
                console.log('Successfully loaded content from:', path);
                return parseMarkdown(content);
            } else {
                 console.log('File not found or fetch error for:', path, 'Status:', response.status);
            }
        } catch (error) {
            console.log('Error loading from', path, ':', error);
        }
        // If fetch failed or file not found, return null
        return null;
    }
    
    // Files to try loading
    const filesToLoad = [
        { fileName: 'description.md', section: 'What is this about?' },
        { fileName: 'data_characteristics.md', section: 'Data Characteristics' },
        { fileName: 'model_characteristics.md', section: 'Model Characteristics' },
        { fileName: 'how_to_use.md', section: 'How to Use It' }
    ];
    
    // Load all files
    totalFetches = filesToLoad.length;
    
    filesToLoad.forEach(async file => {
        const content = await tryLoadFile(file.fileName, file.section);
        if (content) {
            contentSections[file.section] = content;
        }
        fetchesCompleted++;
        
        if (fetchesCompleted === totalFetches) {
            updateDetailPanel();
        }
    });
}

// Function to open the detail panel
function openDetailPanel(title, itemId) {
    const detailPanel = document.getElementById('detailPanel');
    const detailPanelTitle = document.getElementById('detailPanelTitle');
    const detailPanelLoader = document.getElementById('detailPanelLoader');
    const detailPanelData = document.getElementById('detailPanelData');
    const panelOverlay = document.getElementById('panelOverlay');
    
    if (!detailPanel || !detailPanelTitle || !detailPanelLoader || !detailPanelData || !panelOverlay) {
        console.error('Could not find required panel elements');
        return;
    }
    
    // Set title and show panel
    detailPanelTitle.textContent = title;
    detailPanel.classList.add('open');
    panelOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    // Show loader and hide content
    detailPanelLoader.style.display = 'flex';
    detailPanelData.classList.remove('active');
    detailPanelData.style.display = 'none';
    
    // Add share button if it doesn't exist
    let shareButton = detailPanel.querySelector('.share-panel-btn');
    if (!shareButton) {
        shareButton = document.createElement('button');
        shareButton.className = 'share-panel-btn';
        shareButton.innerHTML = '<i class="fas fa-share"></i>';
        shareButton.title = 'Share this view';
        
        // Add click event to copy the current URL
        shareButton.addEventListener('click', function() {
            // Create URL with current item
            const url = new URL(window.location.href);
            url.searchParams.set('item', itemId);
            
            // Copy to clipboard
            navigator.clipboard.writeText(url.href).then(() => {
                // Show success feedback
                const originalHTML = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i>';
                this.classList.add('copied');
                
                // Reset after 2 seconds
                setTimeout(() => {
                    this.innerHTML = originalHTML;
                    this.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy URL: ', err);
            });
        });
        
        // Insert after the close button
        const closeButton = detailPanel.querySelector('.close-panel-btn');
        if (closeButton && closeButton.parentNode) {
            closeButton.parentNode.insertBefore(shareButton, closeButton.nextSibling);
        }
    }
    
    // Load the details
    loadItemDetails(itemId);
}

// Initialize the side panel functionality
document.addEventListener('DOMContentLoaded', function() {
    // Detail Panel Functionality
    const detailPanel = document.getElementById('detailPanel');
    const panelOverlay = document.getElementById('panelOverlay');
    const closeDetailPanel = document.getElementById('closeDetailPanel');
    
    // Add event listeners for detail panel
    document.querySelectorAll('.btn-view-details').forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.card');
            const title = card.getAttribute('data-title');
            const id = card.getAttribute('data-id');
            openDetailPanel(title, id);
        });
    });
    
    if (closeDetailPanel) {
        closeDetailPanel.addEventListener('click', function() {
            detailPanel.classList.remove('open');
            panelOverlay.classList.remove('active');
            document.body.style.overflow = '';
            
            // Reset URL by removing the item parameter
            const url = new URL(window.location.href);
            if (url.searchParams.has('item')) {
                url.searchParams.delete('item');
                window.history.pushState({ path: url.href }, '', url.href);
            }
        });
    }
    
    if (panelOverlay) {
        panelOverlay.addEventListener('click', function() {
            detailPanel.classList.remove('open');
            panelOverlay.classList.remove('active');
            document.body.style.overflow = '';
            
            // Reset URL by removing the item parameter
            const url = new URL(window.location.href);
            if (url.searchParams.has('item')) {
                url.searchParams.delete('item');
                window.history.pushState({ path: url.href }, '', url.href);
            }
        });
    }
}); 