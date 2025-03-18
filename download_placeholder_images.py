#!/usr/bin/env python3
"""
Placeholder Image Downloader for Data Catalog

This script scans all project directories in the data catalog and downloads
relevant placeholder images for projects that don't have images yet.

Usage:
    python download_placeholder_images.py [--api-key YOUR_API_KEY] [--limit 10]

Requirements:
    - requests
    - pandas
    - tqdm
    - python-dotenv

You'll need to set up a Pexels API key (free) at https://www.pexels.com/api/
"""

import os
import re
import json
import argparse
import logging
import random
import time
import requests
import pandas as pd
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

# Load environment variables from .env file if it exists
load_dotenv()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Download placeholder images for data catalog projects.')
    parser.add_argument('--api-key', type=str, help='Pexels API key (or set PEXELS_API_KEY env variable)')
    parser.add_argument('--limit', type=int, default=None, help='Limit the number of projects to process')
    parser.add_argument('--force', action='store_true', help='Force download even if images already exist')
    parser.add_argument('--min-width', type=int, default=800, help='Minimum image width')
    parser.add_argument('--min-height', type=int, default=600, help='Minimum image height')
    parser.add_argument('--data-file', type=str, default='docs/data_catalog.xlsx', help='Path to the data catalog Excel file')
    return parser.parse_args()

def get_project_directories():
    """Get all project directories in the public projects folder."""
    projects_dir = "docs/public/projects"
    if not os.path.exists(projects_dir):
        logger.error(f"Projects directory not found: {projects_dir}")
        return []
    
    return [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]

def has_existing_images(project_dir):
    """Check if a project directory already has images."""
    images_dir = os.path.join("docs/public/projects", project_dir, "images")
    if not os.path.exists(images_dir):
        return False
    
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return len(image_files) > 0

def get_project_info(project_dir, df):
    """Get project title and description from the Excel file."""
    # Normalize the project directory name for comparison
    normalized_dir = project_dir.lower()
    
    # Try to find a matching row in the dataframe
    for _, row in df.iterrows():
        onsite_name = row.get('OnSite Name', '')
        dataset_title = row.get('Dataset Speaking Titles', '')
        usecase_title = row.get('Use Case Speaking Title', '')
        description = row.get('Description - What can be done with this? What is this about?', '')
        domain = row.get('Domain/SDG', '')
        region = row.get('Country Team', '')
        
        # Normalize the titles for comparison
        titles = []
        if isinstance(onsite_name, str) and not pd.isna(onsite_name):
            titles.append(onsite_name)
        if isinstance(dataset_title, str) and not pd.isna(dataset_title):
            titles.append(dataset_title)
        if isinstance(usecase_title, str) and not pd.isna(usecase_title):
            titles.append(usecase_title)
        
        # Check if any of the normalized titles match the project directory
        for title in titles:
            normalized_title = normalize_for_directory(title)
            if normalized_title and normalized_title.lower() == normalized_dir:
                # Found a match
                return {
                    'title': title,
                    'description': description if isinstance(description, str) and not pd.isna(description) else '',
                    'domain': domain if isinstance(domain, str) and not pd.isna(domain) else '',
                    'region': region if isinstance(region, str) and not pd.isna(region) else ''
                }
    
    # If no match found, return None
    return None

def normalize_for_directory(text):
    """Normalize text for use as a directory name."""
    if not isinstance(text, str) or pd.isna(text):
        return ""
    
    # Convert to lowercase, replace spaces with underscores, remove special characters
    normalized = re.sub(r'[^a-z0-9_]', '', text.lower().replace(' ', '_'))
    return normalized

def extract_keywords(project_info):
    """Extract relevant keywords from project title and description."""
    if not project_info:
        return []
    
    # Start with domain and region as they're often good keywords
    keywords = []
    if project_info['domain']:
        # Split domain by commas and semicolons
        domains = re.split(r'[,;]', project_info['domain'])
        keywords.extend([d.strip() for d in domains if d.strip()])
    
    if project_info['region']:
        keywords.append(project_info['region'])
    
    # Extract key terms from title
    title = project_info['title']
    # Remove common filler words
    title_words = re.sub(r'\b(and|the|for|with|in|on|of|to|a|an)\b', ' ', title.lower())
    # Split into words and filter out short words
    title_keywords = [word.strip() for word in title_words.split() if len(word.strip()) > 3]
    keywords.extend(title_keywords[:3])  # Limit to first 3 meaningful words from title
    
    # If we have a description, extract some keywords from it
    if project_info['description']:
        # Get the first sentence or up to 100 characters
        first_part = project_info['description'].split('.')[0][:100]
        # Remove common filler words
        desc_words = re.sub(r'\b(and|the|for|with|in|on|of|to|a|an)\b', ' ', first_part.lower())
        # Split into words and filter out short words
        desc_keywords = [word.strip() for word in desc_words.split() if len(word.strip()) > 3]
        keywords.extend(desc_keywords[:2])  # Limit to first 2 meaningful words from description
    
    # Remove duplicates and empty strings
    keywords = list(set(filter(None, keywords)))
    
    # Limit to 5 keywords max
    return keywords[:5]

def search_pexels_images(keywords, api_key, min_width=800, min_height=600):
    """Search for images on Pexels API based on keywords."""
    if not api_key:
        logger.error("No Pexels API key provided")
        return None
    
    # Join keywords with spaces for the search query
    query = ' '.join(keywords)
    encoded_query = quote_plus(query)
    
    url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page=15&size=medium"
    headers = {
        "Authorization": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Filter images by minimum dimensions
        suitable_images = [
            photo for photo in data.get('photos', [])
            if photo['width'] >= min_width and photo['height'] >= min_height
        ]
        
        if not suitable_images:
            logger.warning(f"No suitable images found for query: {query}")
            return None
        
        # Select a random image from the results
        selected_image = random.choice(suitable_images)
        return {
            'url': selected_image['src']['original'],
            'photographer': selected_image['photographer'],
            'photographer_url': selected_image['photographer_url'],
            'width': selected_image['width'],
            'height': selected_image['height'],
            'pexels_url': selected_image['url']
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching Pexels API: {e}")
        return None
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing Pexels API response: {e}")
        return None

def download_image(image_info, project_dir):
    """Download an image and save it to the project's images directory."""
    if not image_info or not image_info.get('url'):
        return False
    
    images_dir = os.path.join("docs/public/projects", project_dir, "images")
    
    # Create images directory if it doesn't exist
    os.makedirs(images_dir, exist_ok=True)
    
    # Generate a filename with the placeholder prefix
    image_url = image_info['url']
    file_ext = os.path.splitext(image_url.split('?')[0])[1]
    if not file_ext:
        file_ext = '.jpg'  # Default to jpg if no extension found
    
    filename = f"placeholder_image{file_ext}"
    filepath = os.path.join(images_dir, filename)
    
    # Download the image
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Create a metadata file with attribution information
        metadata_path = os.path.join(images_dir, "placeholder_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump({
                'source': 'Pexels',
                'url': image_info['pexels_url'],
                'photographer': image_info['photographer'],
                'photographer_url': image_info['photographer_url'],
                'width': image_info['width'],
                'height': image_info['height'],
                'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        logger.info(f"Downloaded image for {project_dir}: {filepath}")
        return True
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image: {e}")
        return False
    except IOError as e:
        logger.error(f"Error saving image: {e}")
        return False

def main():
    """Main function to download placeholder images for projects without images."""
    args = parse_arguments()
    
    # Get API key from arguments or environment variable
    api_key = args.api_key or os.environ.get('PEXELS_API_KEY')
    if not api_key:
        logger.error("No Pexels API key provided. Use --api-key or set PEXELS_API_KEY environment variable.")
        return
    
    # Load the data catalog Excel file
    try:
        df = pd.read_excel(args.data_file)
        logger.info(f"Loaded data catalog from {args.data_file}")
    except Exception as e:
        logger.error(f"Error loading data catalog: {e}")
        return
    
    # Get all project directories
    project_dirs = get_project_directories()
    logger.info(f"Found {len(project_dirs)} project directories")
    
    # Limit the number of projects to process if specified
    if args.limit and args.limit > 0:
        project_dirs = project_dirs[:args.limit]
        logger.info(f"Limited to processing {args.limit} projects")
    
    # Process each project directory
    success_count = 0
    for project_dir in tqdm(project_dirs, desc="Processing projects"):
        # Skip if project already has images and not forcing download
        if has_existing_images(project_dir) and not args.force:
            logger.debug(f"Skipping {project_dir} - already has images")
            continue
        
        # Get project information
        project_info = get_project_info(project_dir, df)
        if not project_info:
            logger.warning(f"Could not find project info for {project_dir}")
            continue
        
        # Extract keywords for image search
        keywords = extract_keywords(project_info)
        if not keywords:
            logger.warning(f"Could not extract keywords for {project_dir}")
            continue
        
        logger.info(f"Searching for images for {project_dir} with keywords: {', '.join(keywords)}")
        
        # Search for images
        image_info = search_pexels_images(
            keywords, 
            api_key, 
            min_width=args.min_width, 
            min_height=args.min_height
        )
        
        if not image_info:
            logger.warning(f"No suitable images found for {project_dir}")
            continue
        
        # Download the image
        if download_image(image_info, project_dir):
            success_count += 1
        
        # Add a small delay to avoid hitting API rate limits
        time.sleep(1)
    
    logger.info(f"Completed processing. Downloaded {success_count} placeholder images.")

if __name__ == "__main__":
    main() 