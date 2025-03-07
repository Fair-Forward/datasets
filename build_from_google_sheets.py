import argparse
import os
import subprocess
import datetime
import shutil
import pandas as pd
import gspread
import re
from oauth2client.service_account import ServiceAccountCredentials

# Parse command line arguments
parser = argparse.ArgumentParser(description='Fetch data from Google Sheets and build the website.')
parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
parser.add_argument('--backup', action='store_true', help='Create a backup of the existing Excel file')
parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching data from Google Sheets and just build the website')
args = parser.parse_args()

# Create a backup of the existing Excel file only if explicitly requested
if args.backup and os.path.exists(args.output) and not args.skip_fetch:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{os.path.splitext(args.output)[0]}_backup_{timestamp}{os.path.splitext(args.output)[1]}"
    try:
        shutil.copy2(args.output, backup_path)
        print(f"Created backup of existing Excel file at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")

# Function to normalize a string for use as a directory name
def normalize_for_directory(text):
    if not text:
        return ""
    # Convert to lowercase, replace spaces with underscores, remove special characters
    normalized = re.sub(r'[^a-z0-9_]', '', text.lower().replace(' ', '_'))
    return normalized

# Function to create project directories
def create_project_directories(df):
    print("Creating project directories...")
    public_projects_dir = "docs/public/projects"  # Only use public directory
    
    # Create the projects directory if it doesn't exist
    if not os.path.exists(public_projects_dir):
        os.makedirs(public_projects_dir)
    
    # Iterate through each row in the dataframe
    for index, row in df.iterrows():
        title = row.get('OnSite Name', '')
        if not title or pd.isna(title):
            continue
        
        # Normalize the title for use as a directory name
        dir_name = normalize_for_directory(title)
        if not dir_name:
            continue
        
        # Create the project directory
        project_dir = os.path.join(public_projects_dir, dir_name)
        
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            print(f"Created directory: {project_dir}")
        
        # Create images and docs subdirectories
        images_dir = os.path.join(project_dir, "images")
        docs_dir = os.path.join(project_dir, "docs")
        
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir)
        
        # Extract and save additional columns as markdown files
        columns_to_extract = {
            'Description - What can be done with this? What is this about?': 'description.md',
            'Data - Key Characteristics': 'data_characteristics.md',
            'Model/Use-Case - Key Characteristics': 'model_characteristics.md',
            'Deep Dive - How can you concretely work with this and build on this?': 'how_to_use.md'
        }
        
        for column, filename in columns_to_extract.items():
            content = row.get(column, '')
            if content and not pd.isna(content):
                # Create markdown file with the content
                file_path = os.path.join(docs_dir, filename)
                
                # Write the content directly without adding a title
                # The title will be added by the HTML template
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Created file: {file_path}")
        
        # Check for existing project images in the old location and copy them if they exist
        old_images_dir = os.path.join("docs/projects", dir_name, "images")
        if os.path.exists(old_images_dir):
            for image_file in os.listdir(old_images_dir):
                if image_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    src_path = os.path.join(old_images_dir, image_file)
                    dst_path = os.path.join(images_dir, image_file)
                    shutil.copy2(src_path, dst_path)
                    print(f"Copied image: {image_file} to {images_dir}")

# Fetch data from Google Sheets
if not args.skip_fetch:
    print("Fetching data from Google Sheets...")
    try:
        # Setup credentials
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(args.credentials, scope)
        client = gspread.authorize(credentials)
        
        # Extract correct spreadsheet ID and gid from full URL
        full_url = "https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456"
        spreadsheet_id = full_url.split('/d/')[1].split('/')[0]
        gid = 756053104
        
        # Connect to sheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.get_worksheet_by_id(int(gid))
        print(f"Successfully connected to sheet: {sheet.title}")
        
        # Get all values
        all_values = sheet.get_all_values()
        headers = all_values[0]
        data = all_values[1:]
        df = pd.DataFrame(data, columns=headers)
        
        # Save to Excel
        df.to_excel(args.output, index=False)
        print(f"Successfully saved data to {args.output}")
        
        # Create project directories
        create_project_directories(df)
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        exit(1)
else:
    # If skipping fetch, still create project directories from the existing Excel file
    try:
        df = pd.read_excel(args.output)
        create_project_directories(df)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        exit(1)

# Build the website
print("Building the website...")
build_cmd = [
    "python", "generate_catalog.py",
    "--input", args.output
]

try:
    subprocess.run(build_cmd, check=True)
    print("Successfully built the website")
except subprocess.CalledProcessError as e:
    print(f"Error building the website: {e}")
    exit(1)

print("Done!") 