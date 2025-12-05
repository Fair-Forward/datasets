#!/bin/bash

# Script to download placeholder images for the data catalog

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if the script exists
if [ ! -f "download_placeholder_images.py" ]; then
    echo "Error: download_placeholder_images.py not found in the current directory."
    exit 1
fi

# Check if requirements file exists
if [ ! -f "placeholder_images_requirements.txt" ]; then
    echo "Error: placeholder_images_requirements.txt not found in the current directory."
    exit 1
fi

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help                 Show this help message"
    echo "  --install-deps         Install dependencies before running"
    echo "  --api-key KEY          Pexels API key (or set PEXELS_API_KEY env variable)"
    echo "  --limit N              Limit to processing N projects"
    echo "  --force                Force download even if images already exist"
    echo "  --min-width WIDTH      Minimum image width (default: 800)"
    echo "  --min-height HEIGHT    Minimum image height (default: 600)"
    echo ""
    echo "Example:"
    echo "  $0 --install-deps --api-key YOUR_API_KEY --limit 5"
}

# Parse command line arguments
INSTALL_DEPS=false
SCRIPT_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --api-key|--limit|--min-width|--min-height)
            SCRIPT_ARGS="$SCRIPT_ARGS $1 $2"
            shift 2
            ;;
        --force)
            SCRIPT_ARGS="$SCRIPT_ARGS $1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Install dependencies if requested
if [ "$INSTALL_DEPS" = true ]; then
    echo "Installing dependencies..."
    pip install -r placeholder_images_requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies."
        exit 1
    fi
fi

# Run the script
echo "Running placeholder image downloader..."
python3 download_placeholder_images.py $SCRIPT_ARGS

# Check if the script ran successfully
if [ $? -eq 0 ]; then
    echo "Placeholder image download completed successfully."
    echo "Now run 'python3 ../build.py' to rebuild the catalog with the new images."
else
    echo "Error: Placeholder image download failed."
    exit 1
fi 