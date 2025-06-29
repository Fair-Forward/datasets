import argparse
import os
import subprocess
import datetime
import shutil
import pandas as pd
import gspread
import re
import csv
from oauth2client.service_account import ServiceAccountCredentials
from thefuzz import process, fuzz

# Parse command line arguments
parser = argparse.ArgumentParser(description='Fetch data from Google Sheets and build the website.')
parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
parser.add_argument('--backup', action='store_true', help='Create a backup of the existing Excel file')
parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching data from Google Sheets and just build the website')
parser.add_argument('--backup-dir', type=str, default="data_sources/google_sheets_backup", help='Directory to save raw Google Sheet backups')
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
    
    # Check if Project ID column exists (it's critical)
    if 'Project ID' not in df.columns:
        print(f"Error: Critical column 'Project ID' is missing from the DataFrame. Cannot create directories.")
        exit(1)
        
    # Check for content columns (optional, for warnings)
    critical_content_cols = [
        'Description - What can be done with this? What is this about?',
        'Data - Key Characteristics', 'Model/Use-Case - Key Characteristics',
        'Deep Dive - How can you concretely work with this and build on this?'
    ]
    missing_content_cols = [col for col in critical_content_cols if col not in df.columns]
    if missing_content_cols:
        print(f"Warning: Missing content columns, markdown files might be incomplete: {missing_content_cols}")

    # Create the projects directory if it doesn't exist
    if not os.path.exists(public_projects_dir):
        os.makedirs(public_projects_dir)
    
    # Iterate through each row in the dataframe
    for index, row in df.iterrows():
        # --- Get Project ID ---
        project_id = row.get('Project ID', '')
        if not project_id or pd.isna(project_id):
            # print(f"Skipping row {index}: Missing 'Project ID'.") # Less verbose
            continue
            
        # Normalize the Project ID for use as a directory name
        dir_name = normalize_for_directory(str(project_id))
        if not dir_name:
            print(f"Skipping row {index}: Could not normalize Project ID '{project_id}' to a valid directory name.")
            continue

        # --- Determine Display Title (and check if any exists) ---
        display_title = None
        has_real_title = False
        # Check for columns existence before trying to get data
        if 'Dataset Speaking Titles' in df.columns:
            dataset_title = row.get('Dataset Speaking Titles', '')
            if dataset_title and not pd.isna(dataset_title):
                display_title = dataset_title
                has_real_title = True
        
        if not display_title and 'Use Case Speaking Title' in df.columns:
            usecase_title = row.get('Use Case Speaking Title', '')
            if usecase_title and not pd.isna(usecase_title):
                display_title = usecase_title
                has_real_title = True
                
        if not display_title and 'OnSite Name' in df.columns:
            onsite_name = row.get('OnSite Name', '')
            if onsite_name and not pd.isna(onsite_name):
                display_title = onsite_name
                has_real_title = True

        # --- Create Directories and Files ONLY IF Project ID and a Real Title exist ---
        if project_id and has_real_title:
            # Create main project directory (INDENTED)
            project_dir = os.path.join(public_projects_dir, dir_name)
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
                print(f"Created directory: {project_dir}")
            
            # Create images and docs subdirectories (INDENTED)
            images_dir = os.path.join(project_dir, "images")
            docs_dir = os.path.join(project_dir, "docs")
            
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            if not os.path.exists(docs_dir):
                os.makedirs(docs_dir)
                
            # --- START: Clean up old/incorrect .txt title files ---
            correct_normalized_title = normalize_for_directory(str(display_title))
            correct_title_filename = f"{correct_normalized_title}.txt" if correct_normalized_title else None
            
            if correct_title_filename:
                try:
                    for filename in os.listdir(project_dir):
                        # Check if it's a file directly in project_dir and ends with .txt
                        file_path = os.path.join(project_dir, filename)
                        if os.path.isfile(file_path) and filename.endswith('.txt') and filename != correct_title_filename:
                            os.remove(file_path)
                            print(f"Removed old title file: {file_path}")
                except OSError as e:
                    print(f"Error cleaning old title files in {project_dir}: {e}")
            # --- END: Clean up ---
            
            # --- Create empty file named after normalized display title (INDENTED) ---
            if correct_normalized_title: # Ensure title normalization didn't result in empty string
                title_file_path = os.path.join(project_dir, correct_title_filename)
                try:
                    # Create an empty file (or update timestamp if exists)
                    with open(title_file_path, 'a'): 
                        os.utime(title_file_path, None)
                    print(f"Created/Touched title file: {title_file_path}")
                except Exception as e_title:
                    print(f"Error creating/touching title file {title_file_path}: {e_title}")
            else:
                 print(f"Warning: Could not create title file for row {index} because title '{display_title}' normalized to empty string.")

            # --- Extract and save additional columns as markdown files (INDENTED) ---
            columns_to_extract = {
                'Description - What can be done with this? What is this about?': 'description.md',
                'Data - Key Characteristics': 'data_characteristics.md',
                'Model/Use-Case - Key Characteristics': 'model_characteristics.md',
                'Deep Dive - How can you concretely work with this and build on this?': 'how_to_use.md'
            }
            
            for column, filename in columns_to_extract.items():
                if column in df.columns:
                    content = row.get(column, '')
                    # Write file even if content is empty, to ensure old files are overwritten
                    file_path = os.path.join(docs_dir, filename)
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            # Write empty string if content is NaN or None, otherwise write content
                            f.write(str(content) if content and not pd.isna(content) else '') 
                        print(f"Created/Updated file: {file_path}")
                    except Exception as e_md:
                        print(f"Error writing markdown file {file_path}: {e_md}")
                else:
                    # Less verbose logging
                    # print(f"Skipping file {filename} for row {index}: Column '{column}' not found.")
                    pass # Silently skip if column doesn't exist
        else:
            # Skipped because no Project ID or no real title was found
            if project_id:
                print(f"Skipping directory creation for Project ID '{project_id}' (row {index}): No display title found.")
            # No need to print if project_id was missing, already handled

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
        actual_headers = all_values[0]
        # Skip the second row (index 1) which contains explanations
        data = all_values[2:]

        # --- Start: Backup raw data --- 
        if all_values:
            backup_dir = args.backup_dir
            os.makedirs(backup_dir, exist_ok=True)
            # Use only date for the filename
            current_date_str = datetime.datetime.now().strftime("%Y%m%d") 
            backup_filename = f"sheet_backup_{current_date_str}.csv"
            backup_filepath = os.path.join(backup_dir, backup_filename)

            # Check if backup for today already exists
            if not os.path.exists(backup_filepath):
                try:
                    with open(backup_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerows(all_values)
                    print(f"Successfully backed up raw sheet data to {backup_filepath}")
                except Exception as backup_e:
                    print(f"Error writing backup CSV file: {backup_e}")
            else:
                print(f"Skipping backup: Backup file for today ({backup_filename}) already exists.")
        # --- End: Backup raw data ---

        # Define the canonical column names used by scripts and potential aliases in the sheet
        CANONICAL_COLUMN_MAP = {
            # Canonical Name: [List of potential aliases in Google Sheet]
            "Project ID": ["Project ID", "Stable ID", "Unique Project ID"], # Added Project ID
            "OnSite Name": ["OnSite Name", "Name in GIZ-internal database", "Project Title", "Title"],
            "Dataset Speaking Titles": ["Dataset Speaking Titles", "Dataset Title", "Expressive Title [for dataset]"],
            "Use Case Speaking Title": ["Use Case Speaking Title", "Use Case Title", "Expressive Title [for use case, application]"],
            "Description - What can be done with this? What is this about?": [
                "Description - What can be done with this? What is this about?",
                "Description - What can be done", "Description", "About",
                "What this is about and how can I use this? ", # Added from log
                "What this is about/Description" # Added from user input
            ],
            "Dataset Link": ["Dataset Link", "Dataset URL", "Access to the dataset [link]"],
            "Model/Use-Case Links": [
                "Model/Use-Case Links", "Use Case Link", "Model Link", "Model/Use Case URL",
                "Access to AI Model, Software, AI Application [link]" # Added from log
            ],
            "Domain/SDG": ["Domain/SDG", "Domain", "SDG", "Sector /Sustainable Development Goal ", "Technical Domain"],
            "Use Case Pipeline Status": ["Use Case Pipeline Status", "Status", "Pipeline Status", "Use Case Pipeline Status / maturity [INTERNAL]"],
            "Data Type": ["Data Type", "Type", "Type of Data"],
            "Point of Contact/Communities": ["Point of Contact/Communities", "Contact", "POC", "Community", "Point of contact & community support "],
            "Country Team": ["Country Team", "Country", "Region", "Team", "Country / Region "],
            "Data - Key Characteristics": [
                "Data - Key Characteristics", "Data Characteristics", "Data Details",
                "Data: how to use it & key characteristics " # Added from log
                ],
            "Model/Use-Case - Key Characteristics": [
                "Model/Use-Case - Key Characteristics", "Model Characteristics", "Model Details", "Use Case Characteristics",
                "How to use & key characteristics of the AI Model, Software, AI Application" # Added from log
                ],
            "Deep Dive - How can you concretely work with this and build on this?": [
                "Deep Dive - How can you concretely work with this and build on this?",
                "Deep Dive - How can you concretely work", "Deep Dive", "How to Use",
                "Deep dive: How can you concretely work with this and built on this? How much will this cost and which resources are available to help me? " # Added from log
                ],
            "License": ["License", "Usage Rights"],
            # --- Add new columns here ---
            "Organizations Involved": [
                "Organizations involved - including logos, links and visual elements",
                "Organizations Involved", "Contributing Organizations", "Partners"
            ],
            "Authors": [
                "Authors of this information.", "Authors", "Information Authors", "Data Curators"
            ]
            # --- End of new columns ---
        }

        # Identify which canonical columns are absolutely required
        CRITICAL_COLUMNS = [
            "Project ID", # Added Project ID as critical for directory creation
            "Dataset Link", # Needed for generate_catalog.py
            "Description - What can be done with this? What is this about?", # Needed for create_project_dirs
            "Data - Key Characteristics", # Needed for create_project_dirs
            "Model/Use-Case - Key Characteristics", # Needed for create_project_dirs
            "Deep Dive - How can you concretely work with this and build on this?" # Needed for create_project_dirs
        ]

        # --- Start: New Fuzzy Matching Logic ---
        header_mapping = {} # Stores {actual_header: canonical_name}
        found_canonical_headers = set()
        unmatched_critical = []
        similarity_threshold = 70 # Lowered threshold slightly more
        processed_actual_headers = set()

        print("Matching sheet headers to canonical script needs...")
        # Iterate through canonical names we need
        for canonical_name, aliases in CANONICAL_COLUMN_MAP.items():
            best_match_for_canonical = None
            highest_score = -1

            # Find the best actual header matching any alias for this canonical name
            for actual_header in actual_headers:
                if actual_header in processed_actual_headers:
                    continue # Skip if this actual header is already mapped

                # Find the best score against the list of aliases
                match_result = process.extractOne(actual_header, aliases, scorer=fuzz.token_sort_ratio)
                if match_result and match_result[1] > highest_score:
                    highest_score = match_result[1]
                    best_match_for_canonical = actual_header

            # Check if the best match meets the threshold
            if best_match_for_canonical and highest_score >= similarity_threshold:
                # Check if this actual header was already mapped to another canonical name
                # This shouldn't happen with the `processed_actual_headers` check, but as a safeguard:
                if best_match_for_canonical in header_mapping:
                    print(f"  Error: Actual header '{best_match_for_canonical}' unexpectedly mapped twice.")
                    # Decide how to handle - skip this canonical, or overwrite based on score?
                    # For now, let's skip to avoid overwriting a potentially good match
                    continue 

                header_mapping[best_match_for_canonical] = canonical_name
                found_canonical_headers.add(canonical_name)
                processed_actual_headers.add(best_match_for_canonical) # Mark as processed
                print(f"  Mapped: '{best_match_for_canonical}' (Score: {highest_score}) -> '{canonical_name}'")
            else:
                # No suitable match found for this canonical name
                if canonical_name in CRITICAL_COLUMNS:
                    unmatched_critical.append(canonical_name)
                    print(f"  ERROR: Critical column '{canonical_name}' could not be matched! (Best guess: '{best_match_for_canonical}' with score {highest_score})")
                else:
                    print(f"  Warning: Optional column '{canonical_name}' could not be matched. (Best guess: '{best_match_for_canonical}' with score {highest_score})")

        # Abort if critical columns are missing
        if unmatched_critical:
            print(f"Error: Aborting due to missing critical columns: {unmatched_critical}")
            exit(1)
        # --- End: New Fuzzy Matching Logic ---

        # Create DataFrame with original headers first
        df = pd.DataFrame(data, columns=actual_headers)

        # Filter mapping to only include columns present in the DataFrame
        # (Shouldn't be strictly necessary with the new logic but good practice)
        final_mapping = {act: canon for act, canon in header_mapping.items() if act in df.columns}

        # Rename columns based on the successful mapping
        df.rename(columns=final_mapping, inplace=True)
        print("Renamed DataFrame columns based on mapping.")

        # Report any canonical headers that were defined but not found
        unfound_canonicals = set(CANONICAL_COLUMN_MAP.keys()) - found_canonical_headers
        if unfound_canonicals:
            print(f"Note: The following defined canonical columns were not found or mapped: {list(unfound_canonicals)}")

        # Keep only the columns that were successfully mapped to canonical names
        # + any other columns from the sheet that weren't mapped (might be useful)
        final_df_columns = list(final_mapping.values()) + [col for col in df.columns if col not in final_mapping.keys()]
        # Ensure no duplicates (if an original unmapped column name happens to be a canonical name)
        final_df_columns = list(dict.fromkeys(final_df_columns).keys())

        # Select and reorder columns - mapped ones first, then others
        df = df[final_df_columns]
        print(f"Final DataFrame columns: {list(df.columns)}")

        # Save to Excel
        df.to_excel(args.output, index=False)
        print(f"Successfully saved data to {args.output}")
        
        # Create project directories
        create_project_directories(df)
    except gspread.exceptions.APIError as api_e:
        print(f"Google Sheets API Error: {api_e}")
        # Handle specific API errors if needed
        exit(1)
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        # Print traceback for unexpected errors
        import traceback
        traceback.print_exc()
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
    "python", "scripts/generate_catalog.py",
    "--input", args.output
]

try:
    subprocess.run(build_cmd, check=True)
    print("Successfully built the website")
except subprocess.CalledProcessError as e:
    print(f"Error building the website: {e}")
    exit(1)

print("Done!") 