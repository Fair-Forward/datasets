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
from utils import PROJECTS_DIR

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
    if not os.path.exists(PROJECTS_DIR):
        logger.error(f"Projects directory not found: {PROJECTS_DIR}")
        return []
    
    return [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]

def has_existing_images(project_dir):
    """Check if a project directory already has images."""
    images_dir = os.path.join(PROJECTS_DIR, project_dir, "images")
    if not os.path.exists(images_dir):
        return False
    
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return len(image_files) > 0

def get_project_info(project_dir, df):
    """Get project title and description from the Excel file by matching the Project ID."""
    # project_dir is the normalized Project ID (e.g., ui_0)
    target_normalized_id = project_dir.lower()
    
    # Check if 'Project ID' column exists
    if 'Project ID' not in df.columns:
        logger.error("'Project ID' column not found in the DataFrame.")
        return None

    # Try to find a matching row in the dataframe based on Project ID
    for index, row in df.iterrows():
        project_id = row.get('Project ID')
        if project_id and not pd.isna(project_id):
            # Normalize the Project ID from the current row
            current_normalized_id = normalize_for_directory(str(project_id))
            
            # Compare with the target directory name (normalized ID)
            if current_normalized_id == target_normalized_id:
                # Found the matching row based on Project ID
                
                # Now, determine the best *display* title for keyword extraction
                display_title = None
                if 'Dataset Speaking Titles' in df.columns:
                    dataset_title = row.get('Dataset Speaking Titles', '')
                    if dataset_title and not pd.isna(dataset_title):
                        display_title = dataset_title
                
                if not display_title and 'Use Case Speaking Title' in df.columns:
                    usecase_title = row.get('Use Case Speaking Title', '')
                    if usecase_title and not pd.isna(usecase_title):
                        display_title = usecase_title
                        
                if not display_title and 'OnSite Name' in df.columns:
                    onsite_name = row.get('OnSite Name', '')
                    if onsite_name and not pd.isna(onsite_name):
                        display_title = onsite_name
                
                # Fallback display title if none found
                if not display_title:
                    display_title = f"Project {project_id}" # Use raw Project ID if no other title

                # Get other necessary info
                description = row.get('Description - What can be done with this? What is this about?', '')
                domain = row.get('Domain/SDG', '')
                region = row.get('Country Team', '')
                
                # Return the collected info for keyword extraction
                return {
                    'title': display_title, # Use the best display title for keywords
                    'description': description if isinstance(description, str) and not pd.isna(description) else '',
                    'domain': domain if isinstance(domain, str) and not pd.isna(domain) else '',
                    'region': region if isinstance(region, str) and not pd.isna(region) else ''
                    # We could also return project_id if needed later
                }
    
    # If no row matched the Project ID
    logger.warning(f"No row found in Excel matching Project ID directory: {project_dir}")
    return None

def normalize_for_directory(text):
    """Normalize text for use as a directory name."""
    if not isinstance(text, str) or pd.isna(text):
        return ""
    
    # Convert to lowercase, replace spaces with underscores, remove special characters
    normalized = re.sub(r'[^a-z0-9_]', '', text.lower().replace(' ', '_'))
    return normalized

# Define common stop words (expand as needed)
STOP_WORDS = set([
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", 
    "into", "is", "it", "no", "not", "of", "on", "or", "such", "that", "the", 
    "their", "then", "there", "these", "they", "this", "to", "was", "will", "with",
    "using", "based", "dataset", "use-case", "model", "about", "can", "done", 
    "what", "how", "who", "which", "when", "where", "why", "also", "from", 
    "get", "has", "have", "he", "her", "here", "him", "his", "i", "just", "like",
    "make", "many", "me", "might", "more", "most", "my", "never", "now", "our",
    "out", "over", "said", "same", "see", "should", "since", "so", "some", 
    "still", "take", "than", "too", "under", "up", "use", "very", "want", "way",
    "we", "well", "were", "what", "where", "which", "who", "why", "your", "ai",
    "open", "data", "development", "application", "solution" # Added more context-specific words
])

# Define some common technical/domain terms to look for
TECH_TERMS = [
    'satellite', 'imagery', 'remote sensing', 'geospatial', 'map', 'mapping',
    'crop', 'agriculture', 'farming', 'yield', 'harvest',
    'language', 'nlp', 'text', 'speech', 'translation',
    'health', 'medical', 'disease', 'patient', 'clinic',
    'energy', 'power', 'solar', 'wind', 'grid',
    'climate', 'weather', 'environment', 'carbon', 'emission',
    'finance', 'economic', 'market', 'trade',
    'education', 'learning', 'school',
    'water', 'irrigation', 'resource',
    'transport', 'mobility', 'traffic',
    'identification', 'detection', 'classification', 'prediction', 'analysis',
    'monitoring', 'optimization', 'automation', 'platform', 'tool', 'technology',
    'computer vision', 'machine learning'
]

def extract_keywords(project_info, max_keywords=4):
    """Extract relevant keywords from project info, prioritizing specificity."""
    if not project_info:
        return []

    keywords = []
    title = project_info.get('title', '')
    description = project_info.get('description', '')
    domain = project_info.get('domain', '')
    region = project_info.get('region', '')

    # 1. Extract primary domain
    if domain:
        primary_domain = re.split(r'[,;]', domain)[0].strip()
        if primary_domain:
            keywords.append(primary_domain.lower())

    # 2. Extract keywords from title
    if title:
        title_words = re.findall(r'\b\w+\b', title.lower())
        # Prioritize nouns/adjectives, longer words, remove stop words
        potential_title_keywords = [
            word for word in title_words 
            if word not in STOP_WORDS and len(word) > 3
        ]
        # Add the first 1-2 most relevant title words
        keywords.extend(potential_title_keywords[:2])

    # 3. Extract specific terms from description
    if description:
        desc_lower = description.lower()
        found_terms = []
        # Find specific technical terms first
        for term in TECH_TERMS:
            if term in desc_lower:
                found_terms.append(term)
                if len(found_terms) >= 2: # Limit terms from description
                    break
        keywords.extend(found_terms)
        
        # If no tech terms found, try extracting nouns from the first sentence
        if not found_terms:
             first_sentence = description.split('.')[0]
             desc_words = re.findall(r'\b\w+\b', first_sentence.lower())
             potential_desc_keywords = [
                 word for word in desc_words 
                 if word not in STOP_WORDS and len(word) > 4 # Slightly longer words
             ]
             keywords.extend(potential_desc_keywords[:1]) # Add max 1 generic keyword

    # 4. Add region as a fallback/supplement
    if region and len(keywords) < max_keywords:
        keywords.append(region.lower())

    # 5. Refine and finalize
    # Remove duplicates while preserving order (important for keyword priority)
    seen = set()
    unique_keywords = [k for k in keywords if not (k in seen or seen.add(k))]

    # Ensure relevance - if only region/generic domain, add 'technology' or 'data'
    meaningful_keywords = [k for k in unique_keywords if k not in [region.lower() if region else '', primary_domain.lower() if domain else '']]
    if not meaningful_keywords and len(unique_keywords) < max_keywords:
         # Prefer 'technology' if domain is present, else 'data'
        if domain:
            unique_keywords.append('technology')
        else:
            unique_keywords.append('data')

    # Limit the total number of keywords
    final_keywords = unique_keywords[:max_keywords]

    # Basic cleaning (remove plurals for consistency if simple 's' suffix)
    final_keywords = [re.sub(r's$', '', k) if len(k) > 3 else k for k in final_keywords]
    
    # Final duplicate check after cleaning
    seen_final = set()
    final_keywords = [k for k in final_keywords if not (k in seen_final or seen_final.add(k))]


    logger.debug(f"Extracted keywords for '{title}': {final_keywords}")
    return final_keywords

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
    
    images_dir = os.path.join(PROJECTS_DIR, project_dir, "images")
    
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