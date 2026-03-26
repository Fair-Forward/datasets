#!/usr/bin/env python3
"""
Placeholder Image Downloader for Data Catalog

Downloads relevant placeholder images for projects that don't have custom images.
Uses curated SDG-based search queries for much better image relevance.

Supports Pexels and Unsplash APIs (both free).

Usage:
    python download_placeholder_images.py --dry-run                    # preview queries
    python download_placeholder_images.py --force --provider both      # re-download all
    python download_placeholder_images.py --provider unsplash           # unsplash only

Requirements:
    - requests, tqdm, python-dotenv

Set PEXELS_API_KEY and/or UNSPLASH_API_KEY in .env or environment.
"""

import os
import re
import json
import argparse
import logging
import random
import time
import requests
from tqdm import tqdm
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("placeholder_images.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'public', 'projects')

# ---------------------------------------------------------------------------
# Curated SDG-based search queries
# Each SDG maps to a list of search queries known to produce relevant results.
# The script picks one at random per project for visual variety.
# ---------------------------------------------------------------------------
SDG_SEARCH_TERMS = {
    2: [
        "smallholder farming Africa",
        "rice paddy field aerial",
        "agriculture crops developing country",
        "farmer harvest Africa field",
        "maize corn field green",
        "vegetable market Africa",
        "soil agriculture field closeup",
        "irrigation farming rural",
    ],
    3: [
        "health clinic Africa",
        "medical technology stethoscope",
        "rural healthcare developing country",
        "disease prevention health worker",
    ],
    4: [
        "classroom education Africa",
        "students learning technology",
        "school education developing country",
    ],
    5: [
        "women empowerment community",
        "women farmer market Africa",
        "women technology developing country",
        "women leadership Africa",
    ],
    7: [
        "solar panel rural village",
        "renewable energy Africa",
        "solar energy developing country",
        "wind turbine clean energy",
    ],
    8: [
        "marketplace trade Africa",
        "small business entrepreneur",
        "economic growth developing country",
    ],
    9: [
        "technology innovation Africa",
        "infrastructure construction developing",
        "digital technology network",
    ],
    10: [
        "digital inclusion technology Africa",
        "mobile phone rural Africa",
        "language diversity communication",
        "financial inclusion mobile banking",
        "community technology access",
        "voice technology microphone",
    ],
    11: [
        "sustainable city developing country",
        "urban planning Africa aerial",
        "public transport city Africa",
        "smart city infrastructure",
    ],
    12: [
        "sustainable production agriculture",
        "responsible consumption recycling",
    ],
    13: [
        "tropical forest canopy aerial",
        "climate change landscape",
        "deforestation aerial view",
        "mangrove forest coastline",
        "forest conservation green",
        "carbon sequestration trees",
    ],
    14: [
        "ocean marine ecosystem",
        "coastal mangrove water",
        "marine biodiversity coral",
    ],
    15: [
        "biodiversity tropical forest",
        "forest canopy aerial green",
        "tree species tropical",
        "mangrove ecosystem roots",
        "wildlife conservation Africa",
        "national park forest landscape",
    ],
    16: [
        "governance institution justice",
        "peace justice community",
    ],
    17: [
        "partnership collaboration global",
        "international cooperation development",
    ],
}

# Fallback queries when no SDG matches
GENERIC_QUERIES = [
    "data technology Africa",
    "artificial intelligence technology",
    "sustainable development Africa",
    "digital technology developing country",
    "open data technology",
]

# Domain-specific nouns to extract from titles for query refinement
DOMAIN_NOUNS = {
    "mangrove", "maize", "coffee", "rice", "wheat", "cassava", "sorghum",
    "cocoa", "tea", "millet", "banana", "potato", "bean", "groundnut",
    "forest", "tree", "soil", "crop", "livestock", "fishery", "fish",
    "solar", "wind", "grid", "energy", "biogas",
    "health", "medical", "disease", "malaria", "tuberculosis",
    "chatbot", "voice", "language", "speech", "translation", "nlp",
    "drone", "satellite", "sensor", "radar", "lidar",
    "water", "irrigation", "flood", "drought", "rainfall",
    "biodiversity", "species", "conservation", "wildlife", "coral",
    "carbon", "emission", "deforestation", "degradation", "erosion",
    "finance", "loan", "credit", "insurance", "banking",
    "transport", "road", "traffic", "mobility",
    "education", "school", "literacy", "learning",
}

# Data type modifiers appended to queries for specificity
DATA_TYPE_MODIFIERS = {
    "Geospatial/Remote Sensing": "satellite aerial view",
    "Drone Imagery": "drone aerial photography",
    "Meterological": "weather climate data",
    "Meteorological": "weather climate data",
}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Download placeholder images for data catalog projects.')
    parser.add_argument('--provider', choices=['pexels', 'unsplash', 'both'], default='pexels',
                        help='Image provider (default: pexels)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of projects to process')
    parser.add_argument('--force', action='store_true', help='Re-download placeholders (preserves custom images)')
    parser.add_argument('--dry-run', action='store_true', help='Preview search queries without downloading')
    parser.add_argument('--catalog-file', type=str, default='public/data/catalog.json',
                        help='Path to catalog JSON (default: public/data/catalog.json)')
    parser.add_argument('--pexels-key', type=str, help='Pexels API key (or set PEXELS_API_KEY)')
    parser.add_argument('--unsplash-key', type=str, help='Unsplash API key (or set UNSPLASH_API_KEY)')
    return parser.parse_args()


def load_catalog(catalog_file):
    """Load project data from catalog.json."""
    with open(catalog_file, 'r') as f:
        data = json.load(f)
    projects = data.get('projects', data) if isinstance(data, dict) else data
    logger.info(f"Loaded {len(projects)} projects from {catalog_file}")
    return projects


def get_project_directories():
    """Get all project directories."""
    if not os.path.exists(PROJECTS_DIR):
        logger.error(f"Projects directory not found: {PROJECTS_DIR}")
        return []
    return [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]


def has_custom_image(project_dir):
    """Check if a project has a manually-placed (non-placeholder) image."""
    images_dir = os.path.join(PROJECTS_DIR, project_dir, "images")
    if not os.path.exists(images_dir):
        return False
    return any(
        f for f in os.listdir(images_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
        and not f.startswith('placeholder_')
    )


def has_any_image(project_dir):
    """Check if a project has any image at all."""
    images_dir = os.path.join(PROJECTS_DIR, project_dir, "images")
    if not os.path.exists(images_dir):
        return False
    return any(
        f for f in os.listdir(images_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    )


def extract_sdg_number(sdg_label):
    """Extract numeric SDG from label like 'SDG 2'."""
    match = re.search(r'\d+', sdg_label)
    return int(match.group()) if match else None


def extract_domain_nouns(title):
    """Extract unique domain-specific nouns from a project title."""
    if not title:
        return []
    words = re.findall(r'\b\w+\b', title.lower())
    seen = set()
    result = []
    for w in words:
        if w in DOMAIN_NOUNS and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def build_search_query(project_info):
    """Build a search query using SDG-based mapping + title noun refinement.

    Returns a list of queries to try in order (tiered fallback).
    """
    sdgs = project_info.get('sdgs', [])
    title = project_info.get('title', '')
    data_types = project_info.get('data_types', [])

    # Get primary SDG number
    primary_sdg = None
    for sdg_label in sdgs:
        num = extract_sdg_number(sdg_label)
        if num and num in SDG_SEARCH_TERMS:
            primary_sdg = num
            break

    # Extract domain nouns from title
    nouns = extract_domain_nouns(title)

    # Data type modifier
    modifier = ""
    for dt in data_types:
        if dt in DATA_TYPE_MODIFIERS:
            modifier = DATA_TYPE_MODIFIERS[dt]
            break

    queries = []

    if primary_sdg:
        sdg_queries = SDG_SEARCH_TERMS[primary_sdg]

        # Tier 1: SDG query + domain nouns + data type modifier
        if nouns:
            base = random.choice(sdg_queries)
            noun_str = " ".join(nouns[:2])
            tier1 = f"{noun_str} {base}"
            if modifier:
                tier1 = f"{noun_str} {modifier}"
            queries.append(tier1)

        # Tier 2: SDG query with modifier
        tier2 = random.choice(sdg_queries)
        if modifier and not nouns:
            tier2 = f"{tier2} {modifier}"
        queries.append(tier2)

        # Tier 3: Different SDG query (no modifier)
        remaining = [q for q in sdg_queries if q != tier2]
        if remaining:
            queries.append(random.choice(remaining))

    # Tier 4: Generic fallback
    queries.append(random.choice(GENERIC_QUERIES))

    return queries


def search_pexels(query, api_key):
    """Search Pexels for landscape images. Returns image info dict or None."""
    encoded = quote_plus(query)
    url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=15&orientation=landscape"
    headers = {"Authorization": api_key}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        photos = resp.json().get('photos', [])

        # Filter for reasonable dimensions
        suitable = [p for p in photos if p['width'] >= 800 and p['height'] >= 400]
        if not suitable:
            return None

        selected = random.choice(suitable)
        return {
            'download_url': selected['src']['large'],  # 940px wide
            'page_url': selected['url'],
            'photographer': selected['photographer'],
            'photographer_url': selected['photographer_url'],
            'width': selected['width'],
            'height': selected['height'],
            'provider': 'pexels',
        }
    except Exception as e:
        logger.warning(f"Pexels search failed for '{query}': {e}")
        return None


def search_unsplash(query, api_key):
    """Search Unsplash for landscape images. Returns image info dict or None."""
    encoded = quote_plus(query)
    url = f"https://api.unsplash.com/search/photos?query={encoded}&per_page=15&orientation=landscape"
    headers = {"Authorization": f"Client-ID {api_key}"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        results = resp.json().get('results', [])

        # Filter for reasonable dimensions
        suitable = [r for r in results if r['width'] >= 800 and r['height'] >= 400]
        if not suitable:
            return None

        selected = random.choice(suitable)
        return {
            'download_url': selected['urls']['regular'],  # 1080px wide
            'page_url': selected['links']['html'],
            'photographer': selected['user']['name'],
            'photographer_url': selected['user']['links']['html'],
            'width': selected['width'],
            'height': selected['height'],
            'provider': 'unsplash',
        }
    except Exception as e:
        logger.warning(f"Unsplash search failed for '{query}': {e}")
        return None


def search_images(query, provider, pexels_key, unsplash_key):
    """Search for images using the specified provider(s)."""
    if provider == 'pexels' and pexels_key:
        return search_pexels(query, pexels_key)
    elif provider == 'unsplash' and unsplash_key:
        return search_unsplash(query, unsplash_key)
    elif provider == 'both':
        # Try Pexels first, fall back to Unsplash
        if pexels_key:
            result = search_pexels(query, pexels_key)
            if result:
                return result
        if unsplash_key:
            return search_unsplash(query, unsplash_key)
    return None


def download_image(image_info, project_dir, query):
    """Download an image and save it with metadata."""
    if not image_info or not image_info.get('download_url'):
        return False

    images_dir = os.path.join(PROJECTS_DIR, project_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Remove old placeholder if exists
    for old in os.listdir(images_dir):
        if old.startswith('placeholder_'):
            os.remove(os.path.join(images_dir, old))

    # Determine file extension from URL
    download_url = image_info['download_url']
    ext_match = re.search(r'\.(jpe?g|png|webp)', download_url.split('?')[0], re.IGNORECASE)
    file_ext = f".{ext_match.group(1)}" if ext_match else '.jpg'
    filename = f"placeholder_image{file_ext}"
    filepath = os.path.join(images_dir, filename)

    try:
        resp = requests.get(download_url, stream=True, timeout=30)
        resp.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # Save metadata with attribution
        metadata = {
            'source': image_info['provider'].capitalize(),
            'provider': image_info['provider'],
            'search_query': query,
            'url': image_info['page_url'],
            'photographer': image_info['photographer'],
            'photographer_url': image_info['photographer_url'],
            'width': image_info['width'],
            'height': image_info['height'],
            'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        metadata_path = os.path.join(images_dir, "placeholder_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Downloaded image for {project_dir}: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error downloading image for {project_dir}: {e}")
        return False


def find_project_info(project_dir, catalog_projects):
    """Find a project's catalog entry by matching its directory ID."""
    for proj in catalog_projects:
        if proj.get('id') == project_dir:
            return proj
    return None


def main():
    args = parse_arguments()

    pexels_key = args.pexels_key or os.environ.get('PEXELS_API_KEY')
    unsplash_key = args.unsplash_key or os.environ.get('UNSPLASH_API_KEY')

    if not args.dry_run:
        if args.provider in ('pexels', 'both') and not pexels_key:
            logger.info("No Pexels API key available -- skipping Pexels downloads.")
            if args.provider == 'pexels':
                return
        if args.provider in ('unsplash', 'both') and not unsplash_key:
            logger.info("No Unsplash API key available -- skipping Unsplash downloads.")
            if args.provider == 'unsplash':
                return

        if not pexels_key and not unsplash_key:
            logger.info("No image API keys configured. Skipping placeholder image downloads.")
            return

    # Load catalog data
    catalog_projects = load_catalog(args.catalog_file)

    # Get project directories
    project_dirs = get_project_directories()
    logger.info(f"Found {len(project_dirs)} project directories")

    if args.limit and args.limit > 0:
        project_dirs = project_dirs[:args.limit]
        logger.info(f"Limited to {args.limit} projects")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for project_dir in tqdm(project_dirs, desc="Processing projects"):
        # Skip projects with custom (non-placeholder) images
        if has_custom_image(project_dir):
            logger.debug(f"Skipping {project_dir} - has custom image")
            skip_count += 1
            continue

        # Skip projects that already have images (unless --force)
        if has_any_image(project_dir) and not args.force:
            logger.debug(f"Skipping {project_dir} - already has image")
            skip_count += 1
            continue

        # Find project info from catalog
        project_info = find_project_info(project_dir, catalog_projects)
        if not project_info:
            logger.warning(f"No catalog entry for {project_dir}")
            fail_count += 1
            continue

        # Build tiered search queries
        queries = build_search_query(project_info)

        if args.dry_run:
            print(f"\n{project_dir}")
            print(f"  Title: {project_info.get('title', 'N/A')}")
            print(f"  SDGs:  {', '.join(project_info.get('sdgs', []))}")
            print(f"  Queries: {queries}")
            continue

        # Try each query tier until we get a result
        image_info = None
        used_query = None
        for i, query in enumerate(queries):
            logger.info(f"[{project_dir}] Tier {i+1} query: '{query}'")
            image_info = search_images(query, args.provider, pexels_key, unsplash_key)
            if image_info:
                used_query = query
                break
            time.sleep(0.5)  # Brief pause between tiers

        if not image_info:
            logger.warning(f"No image found for {project_dir} after all tiers")
            fail_count += 1
            continue

        if download_image(image_info, project_dir, used_query):
            success_count += 1
        else:
            fail_count += 1

        # Rate limit: ~1.5s between projects
        time.sleep(1.5)

    if not args.dry_run:
        logger.info(f"Done. Downloaded: {success_count}, Skipped: {skip_count}, Failed: {fail_count}")
    else:
        logger.info(f"Dry run complete. Would process {len(project_dirs) - skip_count} projects.")


if __name__ == "__main__":
    main()
