# Theme Toggle System

## Overview

The website now includes a flexible theme toggle system that allows users to switch between different visual themes. The system is designed to be easily extensible for adding new themes in the future.

## Current Themes

1. **Classic** (Default) - Traditional blue and white theme similar to the main branch
2. **Solarized** - Warm, muted colors inspired by the Solarized color scheme

## How It Works

### CSS Architecture

The theme system uses CSS custom properties (variables) to define color schemes:

```css
:root {
    /* Theme-specific variables */
    --classic-primary: #3b5998;
    --solarized-primary: #268bd2;
    
    /* Active theme variables (default to classic) */
    --primary: var(--classic-primary);
}

/* Theme overrides */
[data-theme="solarized"] {
    --primary: var(--solarized-primary);
}
```

### JavaScript Implementation

The theme toggle functionality:
- Cycles through available themes when clicked
- Persists user preference in localStorage
- Updates button text and icon based on current theme
- Applies theme by setting/removing `data-theme` attribute on `<html>`

## Adding New Themes

To add a new theme (e.g., "ocean"):

### 1. Define Theme Variables in CSS

```css
/* Ocean Theme */
--ocean-primary: #0ea5e9;
--ocean-primary-light: #38bdf8;
--ocean-background: #f0f9ff;
--ocean-card-background: #ffffff;
--ocean-text: #0c4a6e;
--ocean-text-light: #075985;
/* ... other variables */
```

### 2. Add Theme Override Section

```css
[data-theme="ocean"] {
    --primary: var(--ocean-primary);
    --primary-light: var(--ocean-primary-light);
    --background: var(--ocean-background);
    --card-background: var(--ocean-card-background);
    --text: var(--ocean-text);
    --text-light: var(--ocean-text-light);
    /* ... other overrides */
}
```

### 3. Update JavaScript Themes Object

```javascript
const themes = {
    'classic': { name: 'Classic', icon: 'fas fa-moon' },
    'solarized': { name: 'Solarized', icon: 'fas fa-sun' },
    'ocean': { name: 'Ocean', icon: 'fas fa-water' }  // Add new theme
};
```

### 4. Update Theme Application Logic (if needed)

The current implementation automatically handles any number of themes through the cycling logic. No changes needed unless you want special handling for specific themes.

## Theme Variables Reference

Each theme should define these core variables:

- `--primary` - Main accent color
- `--primary-light` - Lighter variant for hover states
- `--background` - Main page background
- `--card-background` - Card/section backgrounds
- `--text` - Primary text color
- `--text-light` - Secondary text color
- `--border` - Border color
- `--shadow` - Box shadow color
- `--shadow-hover` - Hover state shadow
- `--title-color` - Heading text color
- `--btn-text` - Text color on primary buttons
- `--yellow` - Accent color for licenses/warnings

## User Experience

- Theme preference is automatically saved and restored on page reload
- Smooth transitions between themes
- Button shows current theme name and appropriate icon
- Accessible keyboard navigation support
- Mobile-responsive design

## Technical Notes

- Uses CSS custom properties for maximum browser compatibility
- Fallback to default theme if invalid theme is stored
- No external dependencies required
- Minimal performance impact
- Works with existing CSS without conflicts 