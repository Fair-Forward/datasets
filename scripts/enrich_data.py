#!/usr/bin/env python3
"""
Data Catalog Enrichment Script

Identifies projects with missing fields in the catalog, fetches metadata from
source links (HuggingFace, GitHub, Zenodo, Kaggle), and writes enrichment
suggestions back to the Google Sheet.

High-confidence data (licenses from structured APIs) is written directly into
empty cells. Lower-confidence extractions (text from READMEs) are written as
[Auto-enrichment] cell notes for human review.

Usage:
    python scripts/enrich_data.py --dry-run                        # preview only
    python scripts/enrich_data.py --dry-run --use-llm              # with LLM extraction
    python scripts/enrich_data.py --write-notes --max-projects 5   # write to sheet (small batch)
    python scripts/enrich_data.py --write-notes                    # full enrichment

Requirements:
    - requests, beautifulsoup4, python-dotenv, pandas, tqdm
    - Optional: OPENROUTER_API_KEY in .env (for --use-llm)
"""

import json
import os
import re
import sys
import time
import argparse
import logging
from datetime import datetime
from difflib import SequenceMatcher
from html import unescape

import requests
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

from utils import (
    get_gsheet_client,
    extract_http_links,
    resolve_project_id,
    DEFAULT_CREDENTIALS_PATH,
)

# Inlined from generate_catalog_data.py to avoid its module-level argparse
LICENSE_NORMALIZATION = {
    'https://creativecommons.org/licenses/by/4.0/': 'CC-BY 4.0',
    'cc-by': 'CC-BY 4.0',
    'cc-by 4.0': 'CC-BY 4.0',
    'cc-by-sa': 'CC-BY-SA 4.0',
    'cc-0': 'CC0 1.0',
    'cc0': 'CC0 1.0',
    'cc-o': 'CC0 1.0',
    'apache 2.0': 'Apache 2.0',
    'apache license 2.0': 'Apache 2.0',
    'mit license': 'MIT',
    'mit': 'MIT',
    'https://www.gnu.org/licenses/agpl-3.0.html': 'AGPL 3.0',
    'https://opendatacommons.org/licenses/dbcl/1-0/': 'ODbL 1.0',
    'permissive': 'Permissive',
    'by-nc-sa-fs': 'BY-NC-SA-FS',
}
KNOWN_LICENSE_VALUES = set(LICENSE_NORMALIZATION.values())


def normalize_license(raw_license):
    """Normalize license strings to canonical short names."""
    if not raw_license or not isinstance(raw_license, str):
        return ''
    cleaned = raw_license.strip()
    if not cleaned or cleaned == 'nan':
        return ''
    lookup = cleaned.lower().strip()
    return LICENSE_NORMALIZATION.get(lookup, cleaned)

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description='Enrich catalog data by fetching metadata from source links.')
parser.add_argument('--input', type=str, default='public/data/catalog.json',
                    help='Path to catalog JSON')
parser.add_argument('--excel', type=str, default='docs/data_catalog.xlsx',
                    help='Path to Excel file (for row mapping with --write-notes)')
parser.add_argument('--credentials', type=str, default=DEFAULT_CREDENTIALS_PATH,
                    help='Path to Google Sheets credentials')
parser.add_argument('--dry-run', action='store_true',
                    help='Preview enrichment without writing to sheet (default behavior)')
parser.add_argument('--write-notes', action='store_true',
                    help='Actually write enrichment to Google Sheet')
parser.add_argument('--use-llm', action='store_true',
                    help='Use LLM API for better extraction from unstructured content')
parser.add_argument('--fields', type=str, default=None,
                    help='Comma-separated list of fields to enrich (default: all)')
parser.add_argument('--project-ids', type=str, default=None,
                    help='Comma-separated project IDs to process (default: all with gaps)')
parser.add_argument('--max-projects', type=int, default=0,
                    help='Limit number of projects to process (0 = all)')
parser.add_argument('--github-token', type=str, default=None,
                    help='GitHub API token for higher rate limits (or GITHUB_TOKEN env var)')
parser.add_argument('--report', type=str, default='docs/enrichment_report.md',
                    help='Path for enrichment report output')
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Column names (reused from validate_data.py)
# ---------------------------------------------------------------------------

COL_LICENSE = 'License'
COL_DESCRIPTION = 'Description - What can be done with this? What is this about?'
COL_DATA_CHARS = 'Data - Key Characteristics'
COL_HOW_TO_USE = 'Deep Dive - How can you concretely work with this and build on this?'
COL_MODEL_CHARS = 'Model/Use-Case - Key Characteristics'
COL_DATASET_LINK = 'Dataset Link'
COL_USECASE_LINKS = 'Model/Use-Case Links'
COL_ADDITIONAL_RESOURCES = 'Link to additional Resources (Paper, Publications, etc)'

COLUMN_ALIASES = {
    COL_LICENSE: ["License", "Usage Rights"],
    COL_DESCRIPTION: [
        "Description - What can be done with this? What is this about?",
        "Description - What can be done", "Description", "About",
        "What this is about and how can I use this? ",
        "What this is about/Description",
    ],
    COL_DATA_CHARS: [
        "Data - Key Characteristics", "Data Characteristics", "Data Details",
        "Data: how to use it & key characteristics ",
        "Data characteristics: how to use it & key characteristics  & Responsible AI Assessments",
    ],
    COL_HOW_TO_USE: [
        "Deep Dive - How can you concretely work with this and build on this?",
        "Deep Dive - How can you concretely work", "Deep Dive", "How to Use",
        "Deep dive: How can you concretely work with this and built on this? "
        "How much will this cost and which resources are available to help me? ",
        "How to use it: How can you concretely work with this and built on this? "
        "How much will this cost and which resources are available to help me?",
    ],
    COL_MODEL_CHARS: [
        "Model/Use-Case - Key Characteristics", "Model Characteristics",
        "Model Details", "Use Case Characteristics",
        "How to use & key characteristics of the AI Model, Software, AI Application",
        "Model characteristics: How to use & key characteristics of the AI Model, "
        "Software, AI Application (if applicable)",
    ],
    COL_ADDITIONAL_RESOURCES: [
        "Link to additional Resources (Paper, Publications, etc)",
        "Additional Resources", "Resources",
    ],
}

FIELD_TO_COLUMN = {
    'license': COL_LICENSE,
    'description': COL_DESCRIPTION,
    'data_characteristics': COL_DATA_CHARS,
    'how_to_use': COL_HOW_TO_USE,
    'model_characteristics': COL_MODEL_CHARS,
}

ENRICHABLE_FIELDS = ['license', 'description', 'data_characteristics',
                     'model_characteristics', 'how_to_use']

# Platform-specific license values -> canonical names
PLATFORM_LICENSE_MAP = {
    'cc-by-4.0': 'CC-BY 4.0',
    'cc-by-sa-4.0': 'CC-BY-SA 4.0',
    'cc0-1.0': 'CC0 1.0',
    'cc-by-nc-4.0': 'CC-BY-NC 4.0',
    'cc-by-nc-sa-4.0': 'CC-BY-NC-SA 4.0',
    'mit': 'MIT',
    'apache-2.0': 'Apache 2.0',
    'agpl-3.0': 'AGPL 3.0',
    'gpl-3.0': 'GPL 3.0',
    'lgpl-3.0': 'LGPL 3.0',
    'bsd-3-clause': 'BSD 3-Clause',
    'bsd-2-clause': 'BSD 2-Clause',
    'odbl': 'ODbL 1.0',
    'odc-by': 'ODC-BY',
    'openrail': 'OpenRAIL',
    'MIT': 'MIT',
    'Apache-2.0': 'Apache 2.0',
    'GPL-3.0': 'GPL 3.0',
    'AGPL-3.0-only': 'AGPL 3.0',
    'CC-BY-4.0': 'CC-BY 4.0',
    'CC0-1.0': 'CC0 1.0',
    'BSD-3-Clause': 'BSD 3-Clause',
    'BSD-2-Clause': 'BSD 2-Clause',
    'ODbL-1.0': 'ODbL 1.0',
    **LICENSE_NORMALIZATION,
}


# ---------------------------------------------------------------------------
# URL classification & parsing
# ---------------------------------------------------------------------------

def classify_url(url):
    """Classify a URL by platform."""
    lower = url.lower()
    if 'huggingface.co' in lower:
        return 'huggingface'
    if 'github.com' in lower:
        return 'github'
    if 'zenodo.org' in lower:
        return 'zenodo'
    if 'doi.org' in lower and '10.5281/zenodo' in lower:
        return 'zenodo'
    if 'kaggle.com' in lower:
        return 'kaggle'
    if 'drive.google.com' in lower or 'docs.google.com' in lower:
        return 'gdrive'  # skipped -- requires auth
    return 'other'


def parse_huggingface_url(url):
    """Parse HuggingFace URL -> (type, api_path) e.g. ('datasets', 'datasets/org/name')."""
    m = re.match(r'https?://huggingface\.co/(datasets/[^/]+/[^/?#]+)', url)
    if m:
        return 'datasets', m.group(1)
    m = re.match(r'https?://huggingface\.co/(?!datasets/)([^/]+/[^/?#]+)', url)
    if m:
        path = m.group(1)
        if path.split('/')[0] in ('spaces', 'papers', 'blog', 'docs', 'tasks'):
            return None, None
        return 'models', path
    return None, None


def parse_github_url(url):
    """Parse GitHub URL -> (owner, repo)."""
    m = re.match(r'https?://github\.com/([^/]+)/([^/?#]+)', url)
    if m:
        owner = m.group(1)
        repo = m.group(2).rstrip('.git')
        if owner in ('topics', 'explore', 'settings', 'orgs'):
            return None, None
        return owner, repo
    return None, None


def parse_zenodo_url(url):
    """Parse Zenodo URL -> record_id."""
    m = re.match(r'https?://zenodo\.org/records?/(\d+)', url)
    if m:
        return m.group(1)
    m = re.match(r'https?://doi\.org/10\.5281/zenodo\.(\d+)', url)
    if m:
        return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Platform fetchers
# ---------------------------------------------------------------------------

def _request_with_retry(url, headers=None, max_retries=2, delay=1.0):
    """GET request with retry logic. Returns response or None."""
    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, headers=headers or {}, timeout=30)
            return resp
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                time.sleep(delay * (attempt + 1))
            else:
                logger.debug(f"Request failed: {url} ({e})")
                return None
    return None


def fetch_huggingface_metadata(url):
    """Fetch metadata from HuggingFace API."""
    hf_type, hf_id = parse_huggingface_url(url)
    if not hf_id:
        return None

    api_url = f'https://huggingface.co/api/{hf_id}'
    resp = _request_with_retry(api_url)
    if not resp or resp.status_code != 200:
        logger.debug(f"HF API failed for {hf_id}: {resp.status_code if resp else 'timeout'}")
        return None

    data = resp.json()
    result = {
        'platform': 'HuggingFace',
        'url': url,
        'license': None,
        'description': data.get('description', '') or '',
        'readme': '',
        'tags': data.get('tags', []),
        'last_modified': data.get('lastModified', ''),
    }

    # License from cardData or tags
    card_data = data.get('cardData', {}) or {}
    if card_data.get('license'):
        lic = card_data['license']
        if isinstance(lic, list):
            lic = lic[0] if lic else ''
        result['license'] = lic
    else:
        for tag in data.get('tags', []):
            if tag.startswith('license:'):
                result['license'] = tag.split(':', 1)[1]
                break

    # Fetch README
    readme_url = f'https://huggingface.co/{hf_id}/raw/main/README.md'
    readme_resp = _request_with_retry(readme_url)
    if readme_resp and readme_resp.status_code == 200:
        result['readme'] = readme_resp.text

    time.sleep(0.5)
    return result


def fetch_github_metadata(url):
    """Fetch metadata from GitHub API."""
    owner, repo = parse_github_url(url)
    if not owner or not repo:
        return None

    token = args.github_token or os.environ.get('GITHUB_TOKEN', '')
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    resp = _request_with_retry(api_url, headers=headers)
    if not resp or resp.status_code != 200:
        logger.debug(f"GitHub API failed for {owner}/{repo}: "
                     f"{resp.status_code if resp else 'timeout'}")
        return None

    remaining = int(resp.headers.get('X-RateLimit-Remaining', 100))
    if remaining < 10:
        reset_time = int(resp.headers.get('X-RateLimit-Reset', 0))
        wait = max(reset_time - time.time(), 0) + 1
        logger.warning(f"GitHub rate limit low ({remaining}), waiting {wait:.0f}s")
        time.sleep(min(wait, 60))

    data = resp.json()
    result = {
        'platform': 'GitHub',
        'url': url,
        'license': None,
        'description': data.get('description', '') or '',
        'readme': '',
        'topics': data.get('topics', []),
        'last_modified': data.get('pushed_at', ''),
    }

    license_info = data.get('license')
    if license_info and license_info.get('spdx_id') and license_info['spdx_id'] != 'NOASSERTION':
        result['license'] = license_info['spdx_id']

    readme_url = f'https://api.github.com/repos/{owner}/{repo}/readme'
    readme_headers = {**headers, 'Accept': 'application/vnd.github.v3.raw'}
    readme_resp = _request_with_retry(readme_url, headers=readme_headers)
    if readme_resp and readme_resp.status_code == 200:
        result['readme'] = readme_resp.text

    time.sleep(0.3)
    return result


def fetch_zenodo_metadata(url):
    """Fetch metadata from Zenodo API."""
    record_id = parse_zenodo_url(url)
    if not record_id:
        if 'doi.org' in url:
            try:
                resp = requests.head(url, allow_redirects=True, timeout=10)
                if resp and 'zenodo.org' in resp.url:
                    record_id = parse_zenodo_url(resp.url)
            except requests.exceptions.RequestException:
                pass
        if not record_id:
            return None

    api_url = f'https://zenodo.org/api/records/{record_id}'
    resp = _request_with_retry(api_url)
    if not resp or resp.status_code != 200:
        logger.debug(f"Zenodo API failed for {record_id}: "
                     f"{resp.status_code if resp else 'timeout'}")
        return None

    data = resp.json()
    metadata = data.get('metadata', {})

    desc = metadata.get('description', '')
    desc = re.sub(r'<[^>]+>', ' ', desc)
    desc = unescape(desc)
    desc = re.sub(r'\s+', ' ', desc).strip()

    result = {
        'platform': 'Zenodo',
        'url': url,
        'license': None,
        'description': desc,
        'readme': '',
        'keywords': metadata.get('keywords', []),
        'last_modified': metadata.get('publication_date', ''),
    }

    license_info = metadata.get('license', {})
    if license_info:
        result['license'] = license_info.get('id', '')

    time.sleep(0.5)
    return result


def fetch_kaggle_metadata(url):
    """Fetch metadata from Kaggle by scraping."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("beautifulsoup4 not installed, skipping Kaggle")
        return None

    headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36'),
    }
    resp = _request_with_retry(url, headers=headers)
    if not resp or resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    result = {
        'platform': 'Kaggle',
        'url': url,
        'license': None,
        'description': '',
        'readme': '',
    }

    meta = soup.find('meta', {'name': 'description'})
    if meta:
        result['description'] = meta.get('content', '')

    for el in soup.find_all(['span', 'div', 'p']):
        text = el.get_text(strip=True)
        if 'license' in text.lower() and len(text) < 100:
            m = re.search(r'(CC[- ]BY[^\s,)]*|MIT|Apache[- ]2\.0|GPL|BSD)', text, re.I)
            if m:
                result['license'] = m.group(1)
                break

    time.sleep(0.5)
    return result


def fetch_generic_metadata(url):
    """Fetch metadata from any web page by scraping HTML content."""
    # Skip Google Drive (requires auth) and non-HTML resources
    lower = url.lower()
    if 'drive.google.com' in lower or 'docs.google.com' in lower:
        return None
    if any(lower.endswith(ext) for ext in ('.pdf', '.zip', '.gz', '.tar', '.csv', '.xlsx')):
        return None

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    resp = _request_with_retry(url, headers=headers)
    if not resp or resp.status_code != 200:
        return None

    content_type = resp.headers.get('Content-Type', '')
    if 'html' not in content_type and 'text' not in content_type:
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Remove script/style elements
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()

    # Extract description from meta tags
    description = ''
    for meta in soup.find_all('meta'):
        if meta.get('name', '').lower() in ('description', 'og:description'):
            description = meta.get('content', '')
            break
        if meta.get('property', '').lower() == 'og:description':
            description = meta.get('content', '')
            break

    # Extract main text content (for LLM extraction)
    main_content = ''
    for container in soup.find_all(['main', 'article']):
        main_content = container.get_text(separator='\n', strip=True)
        break
    if not main_content:
        body = soup.find('body')
        if body:
            main_content = body.get_text(separator='\n', strip=True)

    # Try to find license info
    license_val = None
    text = soup.get_text(separator=' ', strip=True).lower()
    lic_match = re.search(
        r'licen[sc]e[:\s]*(CC[- ]BY[^\s,)]*|MIT|Apache[- ]2\.0|GPL[- ]?3\.0|'
        r'BSD[- ]\d|AGPL|ODbL|CC0|Creative Commons[^,\n]{0,30})',
        text, re.I)
    if lic_match:
        license_val = lic_match.group(1).strip()

    result = {
        'platform': 'Web',
        'url': url,
        'license': license_val,
        'description': description,
        'readme': main_content[:6000] if main_content else '',
    }

    time.sleep(0.5)
    return result


def fetch_metadata_for_project(project):
    """Fetch metadata from all source links for a project. Returns list of metadata dicts."""
    all_urls = []
    for link in project.get('dataset_links', []):
        all_urls.append(link.get('url', ''))
    for link in project.get('usecase_links', []):
        all_urls.append(link.get('url', ''))
    for link in project.get('additional_resources', []):
        all_urls.append(link.get('url', ''))

    fetchers = {
        'huggingface': fetch_huggingface_metadata,
        'github': fetch_github_metadata,
        'zenodo': fetch_zenodo_metadata,
        'kaggle': fetch_kaggle_metadata,
    }

    seen = set()
    results = []
    for url in all_urls:
        if not url or url in seen:
            continue
        seen.add(url)
        platform = classify_url(url)
        fetcher = fetchers.get(platform)
        if fetcher:
            try:
                metadata = fetcher(url)
                if metadata:
                    results.append(metadata)
            except Exception as e:
                logger.debug(f"Error fetching {url}: {e}")
        elif platform == 'other':
            try:
                metadata = fetch_generic_metadata(url)
                if metadata:
                    results.append(metadata)
            except Exception as e:
                logger.debug(f"Error scraping {url}: {e}")

    return results


# ---------------------------------------------------------------------------
# README section extraction (rule-based)
# ---------------------------------------------------------------------------

def strip_yaml_frontmatter(text):
    """Remove YAML front matter from markdown."""
    if text.startswith('---'):
        end = text.find('---', 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


def extract_readme_sections(readme_text):
    """Parse README into sections by headers. Returns {header_lower: text}."""
    if not readme_text:
        return {}

    text = strip_yaml_frontmatter(readme_text)
    sections = {}
    current_header = '_intro'
    current_lines = []

    for line in text.split('\n'):
        m = re.match(r'^#{1,3}\s+(.+)', line)
        if m:
            if current_lines:
                sections[current_header] = '\n'.join(current_lines).strip()
            current_header = m.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_header] = '\n'.join(current_lines).strip()

    return sections


def find_section_content(sections, header_patterns, max_chars=2000):
    """Find first matching section from header patterns."""
    for pattern in header_patterns:
        for header, content in sections.items():
            if pattern in header and content.strip():
                return content[:max_chars]
    return ''


# ---------------------------------------------------------------------------
# LLM extraction (OpenRouter)
# ---------------------------------------------------------------------------

LLM_PROMPTS = {
    'description': (
        "Write a concise, compelling description (3-5 sentences) for a data catalog "
        "aimed at development practitioners, NGOs, and government agencies. "
        "Cover: 1) What specific problem does this dataset/AI application address? "
        "2) Why was it created and what impact can it have? "
        "3) What parts are openly available as a digital public good? "
        "4) Who are the primary beneficiaries -- address them directly if possible "
        "(e.g. 'This can help you as a forest monitoring agency to...'). "
        "Be direct and avoid promotional language. Focus on the story and real-world impact."
    ),
    'data_characteristics': (
        "Write a practical summary of the dataset's key characteristics for someone "
        "considering whether to reuse this data. Cover (where available): "
        "- What the data contains and its format "
        "- Known limitations, imbalances, or biases in the dataset "
        "- Steps taken to ensure responsible and ethical use "
        "- Who maintains and updates the dataset "
        "- What rights users have and under what license the data is published "
        "Write in plain language for development practitioners, not ML researchers."
    ),
    'model_characteristics': (
        "Write a straightforward, easy-to-understand summary of the AI model or application. "
        "Cover (where available): "
        "- What does the model/application do, in simple terms? "
        "- What input does it expect and what output does it produce? "
        "- Known limitations, biases, or ethical considerations "
        "- Steps taken for responsible AI use (e.g. ethical AI assessments) "
        "- Any critical software/hardware requirements for running it "
        "- Please credit source work and note that users should credit it when building new products. "
        "Write for a non-technical audience. Avoid jargon like 'architecture: YOLO' -- "
        "instead say 'uses object detection to identify X in images'."
    ),
    'how_to_use': (
        "Write a practical guide for someone wanting to use or build on this resource. "
        "Start with a concrete, specific opening sentence about what someone can DO -- "
        "never start with 'This is a valuable resource' or similar generic phrasing. "
        "Focus on these priorities: "
        "1) What specific use cases or applications can already be tackled NOW with "
        "the existing tools and resources? What can someone do immediately? "
        "2) How can researchers or developers extend or improve upon this work? "
        "3) Are there critical limitations or biases to consider when replicating "
        "(e.g. 'we recommend going through an ethical AI assessment before replication')? "
        "4) If available: rough cost estimates for building on this (adaptation, training, compute). "
        "Also consider mentioning: opportunities for collaboration, available documentation "
        "or tutorials, success stories, and plans for long-term maintenance or scaling. "
        "Write for development practitioners and innovators, not ML engineers."
    ),
}


def _looks_like_yaml_frontmatter(text):
    """Check if text looks like YAML frontmatter instead of real content."""
    stripped = text.strip()
    yaml_indicators = ['license:', 'task_categories:', 'datasets:', 'language:',
                       'tags:', 'pipeline_tag:', 'model-index:', 'widget:',
                       'base_model:', 'library_name:']
    first_line = stripped.split('\n')[0].strip().lower()
    return any(first_line.startswith(ind) for ind in yaml_indicators)


def llm_extract(text, field_name, project_title, source_url):
    """Use LLM via OpenRouter to extract a field from text. Returns string or ''."""
    # Strip YAML frontmatter before sending to LLM
    text = strip_yaml_frontmatter(text)

    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    base_url = os.environ.get('LLM_BASE_URL', 'https://openrouter.ai/api/v1')
    model = os.environ.get('LLM_MODEL', 'openai/gpt-4o-mini')

    if not api_key:
        return ''

    prompt = LLM_PROMPTS.get(field_name, '')
    if not prompt:
        return ''

    truncated = text[:6000]

    try:
        resp = requests.post(
            f'{base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': (
                        'You write content for a data catalog that showcases open datasets and AI '
                        'use cases for international development. The audience is development '
                        'practitioners, NGOs, government agencies, and innovators in developing '
                        'countries -- not ML researchers. Write in plain, direct language. '
                        'Focus on real-world impact and practical reuse. '
                        'Return only the content text, no commentary or formatting prefixes. '
                        'Write about whatever IS available in the source content -- cover as many '
                        'of the requested aspects as the source material allows, but do not '
                        'fabricate information that is not in the source. '
                        'If there is at least some relevant information, write about it. '
                        'Only respond with "NONE" if the source content has absolutely nothing '
                        'relevant to the requested topic.'
                    )},
                    {'role': 'user', 'content': (
                        f'Project: {project_title}\n'
                        f'Source: {source_url}\n\n'
                        f'{prompt}\n\n'
                        f'Content:\n{truncated}'
                    )},
                ],
                'max_tokens': 800,
                'temperature': 0.1,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            content = (resp.json()
                       .get('choices', [{}])[0]
                       .get('message', {})
                       .get('content', ''))
            if content.strip().upper() == 'NONE':
                return ''
            # Reject output that looks like YAML frontmatter
            if _looks_like_yaml_frontmatter(content):
                logger.debug(f"LLM returned YAML frontmatter for {field_name}, discarding")
                return ''
            return content.strip()
        else:
            logger.debug(f"LLM API returned {resp.status_code}: {resp.text[:200]}")
            return ''
    except Exception as e:
        logger.debug(f"LLM extraction error: {e}")
        return ''
    finally:
        time.sleep(1)


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def extract_license(metadata_list, existing_license):
    """Extract license from platform metadata.
    Returns {'value', 'source_url', 'confidence', 'platform'} or None.
    """
    if existing_license and existing_license.strip():
        return None

    for meta in metadata_list:
        raw = meta.get('license', '')
        if not raw:
            continue

        normalized = PLATFORM_LICENSE_MAP.get(raw)
        if not normalized:
            normalized = PLATFORM_LICENSE_MAP.get(raw.lower())
        if not normalized:
            normalized = normalize_license(raw)

        if normalized and normalized in KNOWN_LICENSE_VALUES:
            return {
                'value': normalized,
                'source_url': meta['url'],
                'confidence': 'high',
                'platform': meta['platform'],
            }

        # Unknown but plausible license string
        if raw and len(raw) < 60:
            return {
                'value': raw,
                'source_url': meta['url'],
                'confidence': 'medium',
                'platform': meta['platform'],
            }

    return None


def extract_text_field(metadata_list, field_name, existing_value,
                       project_title='', use_llm=False, project_context=''):
    """Extract a text field from README content.
    Returns {'value', 'source_url', 'confidence', 'platform'} or None.
    """
    if existing_value and existing_value.strip():
        return None

    header_patterns = {
        'description': ['_intro', 'description', 'about', 'overview',
                        'introduction', 'summary'],
        'data_characteristics': [
            'data', 'dataset', 'features', 'schema', 'format', 'statistics',
            'characteristics', 'specification', 'columns', 'fields',
        ],
        'model_characteristics': [
            'model', 'architecture', 'performance', 'training', 'evaluation',
            'benchmark', 'results', 'specifications',
        ],
        'how_to_use': [
            'usage', 'how to', 'getting started', 'quick start', 'installation',
            'example', 'tutorial', 'quickstart', 'setup',
        ],
    }
    patterns = header_patterns.get(field_name, [])

    for meta in metadata_list:
        readme = meta.get('readme', '')
        # Combine README with API description for richer context
        llm_input = readme
        if not llm_input and meta.get('description'):
            llm_input = meta['description']
        if llm_input and project_context:
            llm_input = f"Existing catalog info:\n{project_context}\n\nSource content:\n{llm_input}"

        # LLM extraction (best quality for unstructured content)
        if use_llm and llm_input and field_name in LLM_PROMPTS:
            extracted = llm_extract(llm_input, field_name, project_title, meta['url'])
            if extracted and len(extracted) >= 20:
                return {
                    'value': extracted,
                    'source_url': meta['url'],
                    'confidence': 'medium',
                    'platform': meta['platform'],
                }

        # Rule-based section extraction from README
        if readme:
            sections = extract_readme_sections(readme)
            content = find_section_content(sections, patterns)
            if content and len(content.strip()) >= 30:
                return {
                    'value': content.strip(),
                    'source_url': meta['url'],
                    'confidence': 'low',
                    'platform': meta['platform'],
                }

            # For description: try first paragraph of intro
            if field_name == 'description' and sections.get('_intro'):
                paragraphs = [p.strip() for p in sections['_intro'].split('\n\n')
                              if p.strip()]
                if paragraphs and len(paragraphs[0]) >= 30:
                    return {
                        'value': paragraphs[0][:1000],
                        'source_url': meta['url'],
                        'confidence': 'low',
                        'platform': meta['platform'],
                    }

        # For description: fall back to API description field
        if field_name == 'description' and meta.get('description'):
            desc = meta['description']
            if len(desc) >= 30:
                return {
                    'value': desc,
                    'source_url': meta['url'],
                    'confidence': 'medium',
                    'platform': meta['platform'],
                }

    return None


# ---------------------------------------------------------------------------
# Additional resource discovery
# ---------------------------------------------------------------------------

ACADEMIC_URL_PATTERNS = [
    r'https?://arxiv\.org/\S+',
    r'https?://doi\.org/\S+',
    r'https?://papers\.ssrn\.com/\S+',
    r'https?://scholar\.google\.com/\S+',
    r'https?://aclanthology\.org/\S+',
    r'https?://proceedings\.\S+',
    r'https?://\S+\.ieee\.org/\S+',
]


def discover_additional_resources(metadata_list, existing_resources):
    """Scan READMEs for academic/paper URLs not already known."""
    existing_urls = {r.get('url', '') for r in (existing_resources or [])}
    source_urls = {m['url'] for m in metadata_list}
    discovered = []

    for meta in metadata_list:
        readme = meta.get('readme', '')
        if not readme:
            continue
        for pattern in ACADEMIC_URL_PATTERNS:
            for match in re.findall(pattern, readme):
                clean = re.sub(r'[.;,)>"\']+$', '', match)
                clean = re.sub(r'\).*$', '', clean)  # strip )—trailing text
                if not clean or clean in existing_urls or clean in source_urls:
                    continue
                discovered.append({
                    'url': clean,
                    'source_url': meta['url'],
                    'platform': meta['platform'],
                })
                existing_urls.add(clean)

    return discovered


# ---------------------------------------------------------------------------
# Cross-reference check
# ---------------------------------------------------------------------------

def cross_reference_description(project, metadata_list):
    """Compare existing description with source. Returns mismatch dict or None."""
    existing = project.get('description', '').strip()
    if not existing or len(existing) < 50:
        return None

    for meta in metadata_list:
        source_desc = meta.get('description', '').strip()
        if not source_desc or len(source_desc) < 30:
            continue

        ratio = SequenceMatcher(None, existing.lower(), source_desc.lower()).ratio()
        if ratio < 0.3:
            return {
                'project_id': project['id'],
                'title': project.get('title', ''),
                'similarity': ratio,
                'source_url': meta['url'],
                'platform': meta['platform'],
                'source_excerpt': source_desc[:200],
                'catalog_excerpt': existing[:200],
            }

    return None


# ---------------------------------------------------------------------------
# Gap identification
# ---------------------------------------------------------------------------

def identify_gaps(catalog_path, target_fields=None, target_project_ids=None):
    """Find projects with missing fields and fetchable source URLs."""
    with open(catalog_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    fields = target_fields or ENRICHABLE_FIELDS
    project_ids = set(target_project_ids) if target_project_ids else None

    gaps = []
    for p in projects:
        if project_ids and p['id'] not in project_ids:
            continue

        missing = []
        for field in fields:
            val = p.get(field, '')
            if not val or not str(val).strip():
                missing.append(field)

        all_urls = []
        for link in p.get('dataset_links', []):
            all_urls.append(link.get('url', ''))
        for link in p.get('usecase_links', []):
            all_urls.append(link.get('url', ''))
        for link in p.get('additional_resources', []):
            all_urls.append(link.get('url', ''))

        has_fetchable = any(
            classify_url(u) not in ('gdrive', '') for u in all_urls if u)
        if has_fetchable:
            p['missing_fields'] = missing
            gaps.append(p)

    return gaps


# ---------------------------------------------------------------------------
# Enrichment report
# ---------------------------------------------------------------------------

def generate_enrichment_report(results, freshness_data, cross_ref_mismatches,
                               discovered_resources, report_path):
    """Generate markdown enrichment report."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    enriched_count = sum(1 for r in results if r.get('enrichments'))
    total_fields = sum(len(r.get('enrichments', {})) for r in results)
    high_conf = sum(
        1 for r in results for e in r.get('enrichments', {}).values()
        if e.get('confidence') == 'high')
    med_conf = sum(
        1 for r in results for e in r.get('enrichments', {}).values()
        if e.get('confidence') == 'medium')
    low_conf = sum(
        1 for r in results for e in r.get('enrichments', {}).values()
        if e.get('confidence') == 'low')

    lines = [
        '# Data Enrichment Report',
        f'Generated: {now}',
        '',
        '## Summary',
        f'- **{len(results)}** projects analyzed',
        f'- **{enriched_count}** projects with enrichable data found',
        f'- **{total_fields}** fields extracted '
        f'({high_conf} high, {med_conf} medium, {low_conf} low confidence)',
        f'- **{len(discovered_resources)}** additional resource links discovered',
        f'- **{len(cross_ref_mismatches)}** description mismatches flagged',
        '',
    ]

    # Enrichment table
    if any(r.get('enrichments') for r in results):
        lines.append('## Enrichment Results')
        lines.append('')
        lines.append('| Project | Field | Source | Confidence | Value (excerpt) |')
        lines.append('|---|---|---|---|---|')
        for r in results:
            for field, e in r.get('enrichments', {}).items():
                title = r['title'][:40]
                excerpt = e['value'][:60].replace('|', '\\|').replace('\n', ' ')
                lines.append(
                    f"| {title} | {field} | {e.get('platform', '?')} "
                    f"| {e['confidence']} | {excerpt} |")
        lines.append('')

    # Discovered resources
    if discovered_resources:
        lines.append('## Additional Resources Discovered')
        lines.append('')
        lines.append('| Project | Discovered URL | Found In |')
        lines.append('|---|---|---|')
        for item in discovered_resources:
            title = item.get('project_title', '?')[:40]
            lines.append(f"| {title} | {item['url']} | {item['platform']} |")
        lines.append('')

    # Cross-reference mismatches
    if cross_ref_mismatches:
        lines.append('## Description Mismatches')
        lines.append('')
        lines.append('Projects with descriptions that differ significantly '
                     'from their source pages.')
        lines.append('')
        for mm in cross_ref_mismatches:
            lines.append(f"### {mm['title']}")
            lines.append(f"- **Similarity**: {mm['similarity']:.0%}")
            lines.append(f"- **Source**: {mm['source_url']} ({mm['platform']})")
            lines.append(f"- **Catalog excerpt**: {mm['catalog_excerpt']}...")
            lines.append(f"- **Source excerpt**: {mm['source_excerpt']}...")
            lines.append('')

    # Freshness
    if freshness_data:
        lines.append('## Data Freshness')
        lines.append('')
        lines.append('| Project | Platform | Last Updated |')
        lines.append('|---|---|---|')
        for item in freshness_data:
            title = item.get('title', '?')[:40]
            lines.append(
                f"| {title} | {item['platform']} | {item['last_modified']} |")
        lines.append('')

    # No enrichment
    no_enrichment = [r for r in results
                     if not r.get('enrichments') and r.get('missing_fields')]
    if no_enrichment:
        lines.append('## Projects Without Enrichable Data')
        lines.append('')
        for r in no_enrichment:
            missing = ', '.join(r['missing_fields'])
            lines.append(f"- **{r['title'][:60]}** -- missing: {missing}")
        lines.append('')

    os.makedirs(os.path.dirname(report_path) or '.', exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"\nEnrichment report written to {report_path}")


# ---------------------------------------------------------------------------
# Sheet writing (direct cell writes with disclaimer)
# ---------------------------------------------------------------------------

CELL_DISCLAIMER = "[Auto-enriched from linked project resources]\n\n"


def write_enrichment_to_sheet(results, discovered_resources,
                              excel_path, credentials_path):
    """Write enrichment directly into empty Google Sheet cells.
    License fields: written without disclaimer (factual structured data).
    Text fields: prefixed with disclaimer line.
    Never overwrites non-empty cells.
    """
    import gspread
    _client, _spreadsheet, sheet = get_gsheet_client(credentials_path)
    headers = sheet.row_values(1)

    header_to_idx = {}
    for i, h in enumerate(headers):
        header_to_idx[h.strip()] = i + 1

    col_indices = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            stripped = alias.strip()
            if stripped in header_to_idx:
                col_indices[canonical] = header_to_idx[stripped]
                if stripped != canonical:
                    print(f"  Matched column '{canonical}' -> '{stripped}'")
                break
        if canonical not in col_indices:
            logger.warning(f"Could not find sheet column for '{canonical}'")

    # Build project_id -> Excel row index mapping
    df = pd.read_excel(excel_path)
    id_to_row_idx = {}
    for idx, row in df.iterrows():
        pid, _src, _err = resolve_project_id(row, row_idx=idx)
        if pid:
            id_to_row_idx[pid] = idx

    # Read existing cell values
    all_values = sheet.get_all_values()

    def get_cell_value(sheet_row, col_idx):
        r, c = sheet_row - 1, col_idx - 1
        if r < len(all_values) and c < len(all_values[r]):
            return all_values[r][c].strip()
        return ''

    batch_cells = []  # list of {'range': A1, 'values': [[val]]}

    for result in results:
        row_idx = id_to_row_idx.get(result.get('id'))
        if row_idx is None:
            continue
        sheet_row = row_idx + 3

        for field, enrichment in result.get('enrichments', {}).items():
            col_name = FIELD_TO_COLUMN.get(field)
            if not col_name:
                continue
            col_idx = col_indices.get(col_name)
            if col_idx is None:
                continue

            cell = gspread.utils.rowcol_to_a1(sheet_row, col_idx)
            current_value = get_cell_value(sheet_row, col_idx)

            if current_value:
                continue  # never overwrite

            if field == 'license':
                # License: no disclaimer needed (structured data)
                cell_value = enrichment['value']
            else:
                # Text fields: add disclaimer prefix
                cell_value = CELL_DISCLAIMER + enrichment['value']

            batch_cells.append({
                'range': cell,
                'values': [[cell_value]],
            })

    # Execute writes
    if batch_cells:
        try:
            sheet.batch_update(batch_cells)
            print(f"  Wrote {len(batch_cells)} cell values to Google Sheet")
        except Exception as e:
            print(f"  Error writing cell values: {e}")
    else:
        print("  No enrichment data to write.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found. Run generate_catalog_data.py first.")
        sys.exit(1)

    if args.use_llm and not os.environ.get('OPENROUTER_API_KEY'):
        print("Warning: --use-llm set but OPENROUTER_API_KEY not found in .env")
        print("LLM extraction will be skipped. Set the key in .env or environment.")

    # Parse filters
    target_fields = None
    if args.fields:
        target_fields = [f.strip() for f in args.fields.split(',')]
        invalid = [f for f in target_fields if f not in ENRICHABLE_FIELDS]
        if invalid:
            print(f"Error: Unknown fields: {', '.join(invalid)}")
            print(f"Valid fields: {', '.join(ENRICHABLE_FIELDS)}")
            sys.exit(1)

    target_project_ids = None
    if args.project_ids:
        target_project_ids = [p.strip() for p in args.project_ids.split(',')]

    # Identify gaps
    print("Identifying projects with missing fields...")
    gaps = identify_gaps(args.input, target_fields, target_project_ids)

    if args.max_projects > 0:
        gaps = gaps[:args.max_projects]

    if not gaps:
        print("No projects with missing fields and fetchable source URLs found.")
        sys.exit(0)

    gaps_with_missing = [g for g in gaps if g.get('missing_fields')]
    print(f"Found {len(gaps_with_missing)} projects with missing fields "
          f"({len(gaps)} total with fetchable URLs)")

    # Enrich
    results = []
    freshness_data = []
    cross_ref_mismatches = []
    all_discovered_resources = []

    for project in tqdm(gaps, desc="Enriching projects"):
        title = project.get('title', project['id'])
        metadata_list = fetch_metadata_for_project(project)

        if not metadata_list:
            results.append({
                'id': project['id'],
                'title': title,
                'missing_fields': project.get('missing_fields', []),
                'enrichments': {},
            })
            continue

        enrichments = {}
        for field in project.get('missing_fields', []):
            if target_fields and field not in target_fields:
                continue

            if field == 'license':
                extraction = extract_license(
                    metadata_list, project.get('license', ''))
            else:
                # Build context from existing catalog fields
                ctx_parts = []
                if project.get('description'):
                    ctx_parts.append(f"Description: {project['description'][:500]}")
                if project.get('data_characteristics'):
                    ctx_parts.append(f"Data: {project['data_characteristics'][:300]}")
                if project.get('model_characteristics'):
                    ctx_parts.append(f"Model: {project['model_characteristics'][:300]}")
                project_context = '\n'.join(ctx_parts)

                extraction = extract_text_field(
                    metadata_list, field, project.get(field, ''),
                    project_title=title, use_llm=args.use_llm,
                    project_context=project_context)

            if extraction:
                enrichments[field] = extraction

        # Freshness tracking
        for meta in metadata_list:
            last_mod = meta.get('last_modified', '')
            if last_mod:
                freshness_data.append({
                    'project_id': project['id'],
                    'title': title,
                    'platform': meta['platform'],
                    'last_modified': last_mod,
                    'source_url': meta['url'],
                })

        # Cross-reference
        mismatch = cross_reference_description(project, metadata_list)
        if mismatch:
            cross_ref_mismatches.append(mismatch)

        # Resource discovery
        discovered = discover_additional_resources(
            metadata_list, project.get('additional_resources', []))
        for d in discovered:
            d['project_id'] = project['id']
            d['project_title'] = title
        all_discovered_resources.extend(discovered)

        results.append({
            'id': project['id'],
            'title': title,
            'missing_fields': project.get('missing_fields', []),
            'enrichments': enrichments,
        })

    # Summary
    enriched = sum(1 for r in results if r.get('enrichments'))
    total_fields = sum(len(r.get('enrichments', {})) for r in results)
    print(f"\n{'='*60}")
    print(f"ENRICHMENT SUMMARY")
    print(f"{'='*60}")
    print(f"  {len(results)} projects analyzed")
    print(f"  {enriched} projects with enrichable data found")
    print(f"  {total_fields} fields extracted")
    print(f"  {len(all_discovered_resources)} additional resource links discovered")
    print(f"  {len(cross_ref_mismatches)} description mismatches flagged")
    print(f"{'='*60}")

    # Report
    generate_enrichment_report(
        results, freshness_data, cross_ref_mismatches,
        all_discovered_resources, args.report)

    # Write to sheet
    if args.write_notes:
        if not os.path.exists(args.credentials):
            print(f"Error: Credentials file '{args.credentials}' not found.")
            sys.exit(1)
        if not os.path.exists(args.excel):
            print(f"Error: Excel file '{args.excel}' not found.")
            sys.exit(1)

        print("\nWriting enrichment to Google Sheet...")
        write_enrichment_to_sheet(
            results, all_discovered_resources,
            args.excel, args.credentials)
    else:
        print("\nDry run complete. Use --write-notes to write to Google Sheet.")
