# Placeholder Image Downloader

This script automatically downloads relevant placeholder images for projects in the data catalog that don't have images yet. It uses the Pexels API to find high-quality, free-to-use images based on keywords extracted from the project title, description, domain, and region.

## Features

- Scans all project directories in the data catalog
- Extracts relevant keywords from project metadata
- Searches for images using the Pexels API
- Downloads images and saves them with a "placeholder_" prefix
- Creates metadata files with attribution information
- Configurable via command-line arguments
- Detailed logging

## Setup

1. Install the required dependencies:

```bash
pip install -r placeholder_images_requirements.txt
```

2. Get a free API key from Pexels:
   - Sign up at https://www.pexels.com/api/
   - Create a new API key

3. Set up your API key in one of two ways:
   - Create a `.env` file with `PEXELS_API_KEY=your_api_key_here`
   - Pass the API key as a command-line argument

## Usage

Basic usage:

```bash
python download_placeholder_images.py --api-key YOUR_API_KEY
```

With environment variable:

```bash
# After setting PEXELS_API_KEY in .env or environment
python download_placeholder_images.py
```

Additional options:

```bash
# Limit to processing 5 projects
python download_placeholder_images.py --limit 5

# Force download even if images already exist
python download_placeholder_images.py --force

# Specify minimum image dimensions
python download_placeholder_images.py --min-width 1200 --min-height 800

# Specify a different data catalog file
python download_placeholder_images.py --data-file path/to/catalog.xlsx
```

## How It Works

1. The script scans all project directories in `public/projects`
2. For each project without images, it:
   - Finds the corresponding entry in the data catalog Excel file
   - Extracts keywords from the title, description, domain, and region
   - Searches for relevant images using the Pexels API
   - Downloads a suitable image and saves it as `placeholder_image.jpg` (or other extension)
   - Creates a `placeholder_metadata.json` file with attribution information

## Image Attribution

All downloaded images come from Pexels and are free to use. However, it's good practice to provide attribution. The script automatically creates a metadata file with the photographer's name and link for each downloaded image.

## Updating the Catalog

When new projects are added to the data catalog, simply run the script again to download placeholder images for the new projects. Existing projects with images will be skipped unless you use the `--force` flag.

## Troubleshooting

If you encounter any issues:

1. Check the `placeholder_images.log` file for detailed error messages
2. Make sure your API key is valid
3. Check your internet connection
4. Try running with the `--force` flag to re-download images

## License

This script is provided under the same license as the main project. 