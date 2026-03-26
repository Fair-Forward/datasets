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


def snapshot_project_images():
    """Return set of image file paths under public/projects/*/images/."""
    images = set()
    projects_dir = os.path.join('public', 'projects')
    if not os.path.isdir(projects_dir):
        return images
    for project in os.listdir(projects_dir):
        img_dir = os.path.join(projects_dir, project, 'images')
        if os.path.isdir(img_dir):
            for f in os.listdir(img_dir):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    images.add(os.path.join(img_dir, f))
    return images

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
    
    # Step 1b: Run data quality validation (advisory, never blocks the build)
    subprocess.run(
        [PYTHON, 'scripts/validate_data.py', '--check-urls'],
        check=False
    )

    # Step 1c: Diff catalog to detect suspicious changes
    # At this point public/data/catalog.json is new, docs/data/catalog.json is still old
    print(f"\n{'='*60}")
    print(f"  Comparing catalog changes (security check)")
    print(f"{'='*60}")
    diff_result = subprocess.run(
        [PYTHON, 'scripts/diff_catalog.py'],
        capture_output=True, text=True
    )
    if diff_result.returncode == 1:
        # Script detected suspicious changes
        with open('change_summary.md', 'w') as f:
            f.write(diff_result.stdout)
        with open('.diff_exit_code', 'w') as f:
            f.write('1')
        print(diff_result.stdout)
        print("Build will continue, but the deployment workflow will flag this for review.")
    elif diff_result.returncode == 0:
        # Normal changes
        with open('change_summary.md', 'w') as f:
            f.write(diff_result.stdout)
        with open('.diff_exit_code', 'w') as f:
            f.write('0')
        print(diff_result.stdout)
    else:
        # Script crashed -- treat as safe to avoid blocking deploys, but warn
        print(f"Warning: diff_catalog.py exited with code {diff_result.returncode}")
        if diff_result.stderr:
            print(f"  stderr: {diff_result.stderr.strip()}")
        with open('change_summary.md', 'w') as f:
            f.write("## Sheet Update Summary\n\nChange detection script encountered an error. "
                    "Changes were not analyzed but the build proceeded.\n")
        with open('.diff_exit_code', 'w') as f:
            f.write('0')

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
    
    # Step 3: Download placeholder images for projects without images
    # Runs only when API keys are available (via env vars or .env file)
    images_before = snapshot_project_images()

    print(f"\n{'='*60}")
    print(f"  Downloading placeholder images (if API keys available)")
    print(f"{'='*60}")
    result = subprocess.run(
        [PYTHON, 'scripts/download_placeholder_images.py', '--limit', '10'],
        check=False  # Never fail the build due to image downloads
    )
    if result.returncode != 0:
        print("Warning: Placeholder image download encountered an error (non-fatal)")

    images_after = snapshot_project_images()
    new_images = images_after - images_before

    if new_images:
        print(f"\n{len(new_images)} new placeholder image(s) downloaded.")
        print("Regenerating catalog.json to include new image paths...")
        if not run_command(
            [PYTHON, 'scripts/generate_catalog_data.py'],
            "Regenerating catalog data (with new images)"
        ):
            sys.exit(1)
    else:
        print("No new images downloaded; skipping catalog regeneration.")

    # Step 4: Clean stale project directories from docs/
    # Vite's emptyOutDir:false preserves old dirs; remove any not in public/projects/
    docs_projects = os.path.join('docs', 'projects')
    public_projects = os.path.join('public', 'projects')
    if os.path.isdir(docs_projects) and os.path.isdir(public_projects):
        source_dirs = set(os.listdir(public_projects))
        stale = [d for d in os.listdir(docs_projects)
                 if os.path.isdir(os.path.join(docs_projects, d)) and d not in source_dirs]
        if stale:
            import shutil
            for d in stale:
                shutil.rmtree(os.path.join(docs_projects, d))
            print(f"Removed {len(stale)} stale project directories from docs/projects/")

    # Step 5: Build React application
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

