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
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" class="panel-link"><i class="fas fa-external-link-alt"></i> $1</a>');
    
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
    const dirNamesStr = card.getAttribute('data-dir-names');
    
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
    
    // Get dataset and use-case links
    const datasetLink = card.querySelector('.btn-primary[href]');
    const useCaseLink = card.querySelector('.btn-secondary[href]');
    
    // Get data type chips
    const dataTypeChips = Array.from(card.querySelectorAll('.data-type-chip')).map(chip => {
        const chipClass = Array.from(chip.classList).find(c => c.startsWith('label-'));
        console.log('Data type chip class:', chipClass, 'from', chip.classList);
        return {
            text: chip.textContent.trim(),
            class: chipClass,
            filter: chip.getAttribute('data-filter')
        };
    });
    
    // Get domain badges
    const domainBadges = Array.from(card.querySelectorAll('.domain-badge')).map(badge => {
        const badgeClass = Array.from(badge.classList).find(c => c.startsWith('domain-'));
        console.log('Domain badge class:', badgeClass, 'from', badge.classList);
        return {
            text: badge.textContent.trim(),
            class: badgeClass
        };
    });
    
    // Parse the directory names from the data attribute
    let dirNames = [];
    try {
        dirNames = JSON.parse(dirNamesStr.replace(/'/g, '"'));
    } catch (e) {
        console.error('Error parsing directory names:', e);
        // Fallback to old behavior
        dirNames = [title.toLowerCase().replace(/ /g, '_').replace(/[^a-z0-9_]/g, '')];
    }
    
    console.log('Possible directory names:', dirNames);
    
    // Show loading state
    const detailPanelLoader = document.getElementById('detailPanelLoader');
    const detailPanelData = document.getElementById('detailPanelData');
    
    if (detailPanelLoader && detailPanelData) {
        detailPanelLoader.style.display = 'flex';
        detailPanelData.style.display = 'none';
    }
    
    // Initialize content sections
    let contentSections = {
        'What is this about and how can I use this?': '',
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
        
        // Add data type chips
        if (dataTypeChips.length > 0) {
            detailContent += `<div class="panel-data-type-chips">`;
            dataTypeChips.forEach(chip => {
                // Extract icon class from the original chip
                const iconMatch = chip.text.match(/^(\s*<i class="fas ([^"]+)"><\/i>\s*)(.*)$/);
                const iconClass = iconMatch ? iconMatch[2] : 'fa-database';
                const chipText = iconMatch ? iconMatch[3].trim() : chip.text.trim();
                
                const chipHTML = `<span class="panel-data-type-chip ${chip.class || ''}" data-filter="${chip.filter || ''}">
                    <i class="fas ${iconClass}"></i> ${chipText}
                </span>`;
                console.log('Generated data type chip HTML:', chipHTML);
                detailContent += chipHTML;
            });
            detailContent += `</div>`;
        }
        
        // Add links section
        detailContent += `<div class="panel-links-section">`;
        if (datasetLink) {
            detailContent += `<a href="${datasetLink.getAttribute('href')}" target="_blank" class="panel-link-btn panel-dataset-link">
                <i class="fas fa-database"></i> View Dataset
            </a>`;
        }
        if (useCaseLink) {
            detailContent += `<a href="${useCaseLink.getAttribute('href')}" target="_blank" class="panel-link-btn panel-usecase-link">
                <i class="fas fa-lightbulb"></i> View Use Case
            </a>`;
        }
        detailContent += `</div>`;
        
        detailContent += `</div>`; // Close panel-title-section
        
        // Create a table of contents if we have multiple sections
        let hasMultipleSections = Object.values(contentSections).filter(Boolean).length > 1;
        
        if (hasMultipleSections) {
            let tocContent = '<div class="panel-toc">';
            tocContent += '<div class="panel-toc-title"><i class="fas fa-list"></i> Contents</div>';
            tocContent += '<ul class="panel-toc-list">';
            
            // Add TOC items for each section with content
            for (const [section, content] of Object.entries(contentSections)) {
                if (content) {
                    const sectionId = section.toLowerCase().replace(/\s+/g, '-');
                    let icon = 'fa-file-alt';
                    
                    // Choose appropriate icon for each section
                    if (section.includes('Data')) {
                        icon = 'fa-database';
                    } else if (section.includes('Model')) {
                        icon = 'fa-robot';
                    } else if (section.includes('How to Use')) {
                        icon = 'fa-lightbulb';
                    } else if (section.includes('What is this about')) {
                        icon = 'fa-info-circle';
                    }
                    
                    tocContent += `<li class="panel-toc-item">
                        <a href="#${sectionId}" class="panel-toc-link">
                            <i class="fas ${icon}"></i> ${section}
                        </a>
                    </li>`;
                }
            }
            
            tocContent += '</ul></div>';
            detailContent += tocContent;
        }
        
        // Add each section that has content
        for (const [section, content] of Object.entries(contentSections)) {
            if (content) {
                const sectionId = section.toLowerCase().replace(/\s+/g, '-');
                detailContent += `
                    <div class="detail-section" id="${sectionId}">
                        <h3 data-section="${section}">${section}</h3>
                        <div class="documentation-content">${content}</div>
                    </div>
                `;
            }
        }
        
        // Add region section if available with enhanced styling
        if (region) {
            detailContent += `
                <div class="detail-section" id="region">
                    <h3 data-section="Region">Region</h3>
                    <div class="documentation-content">
                        <p><i class="fas fa-map-marker-alt"></i> ${region}</p>
                    </div>
                </div>
            `;
        }
        
        // Add tags section with enhanced styling
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
        for (const dirName of dirNames) {
            const path = `./public/projects/${dirName}/docs/${fileName}`;
            console.log('Trying to load from:', path);
            try {
                const response = await fetch(path);
                if (response.ok) {
                    const content = await response.text();
                    console.log('Successfully loaded content from:', path);
                    return parseMarkdown(content);
                }
            } catch (error) {
                console.log('Error loading from', path, ':', error);
            }
        }
        return null;
    }
    
    // Files to try loading
    const filesToLoad = [
        { fileName: 'description.md', section: 'What is this about and how can I use this?' },
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
        shareButton.innerHTML = '<i class="fas fa-share-alt"></i>';
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
        });
    }
    
    if (panelOverlay) {
        panelOverlay.addEventListener('click', function() {
            detailPanel.classList.remove('open');
            panelOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
}); 