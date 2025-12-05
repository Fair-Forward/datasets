#!/usr/bin/env python3
"""
Master build script for Fair Forward Data Catalog

Orchestrates the complete build process:
1. Generate JSON data files from Excel
2. Build React application  
3. Output to docs/ for GitHub Pages
"""

import subprocess
import sys
import os

PYTHON = sys.executable

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  Fair Forward Data Catalog - Complete Build")
    print("="*60)
    
    # Step 1: Generate catalog JSON
    if not run_command(
        [PYTHON, 'scripts/generate_catalog_data.py'],
        "Generating catalog data (JSON)"
    ):
        sys.exit(1)
    
    # Step 2: Generate insights JSON  
    # Read project count from catalog.json
    import json
    try:
        with open('public/data/catalog.json', 'r') as f:
            catalog = json.load(f)
            project_count = catalog['stats']['total_projects']
    except:
        project_count = 60  # Fallback
    
    if not run_command(
        [PYTHON, 'scripts/generate_insights_data.py', '--project-count', str(project_count)],
        "Generating insights data (JSON)"
    ):
        sys.exit(1)
    
    # Step 3: Build React application
    if not run_command(
        ['npm', 'run', 'build'],
        "Building React application (Vite)"
    ):
        sys.exit(1)
    
    print("\n" + "="*60)
    print("  ✅ BUILD COMPLETE!")
    print("="*60)
    print("\nOutput directory: docs/")
    print("Ready for GitHub Pages deployment")
    print("\nTo preview locally:")
    print("  npm run preview")
    print("\nTo develop locally:")
    print("  npm run dev")
    print()

if __name__ == "__main__":
    main()

