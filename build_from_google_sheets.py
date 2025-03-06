import argparse
import os
import subprocess
import datetime
import shutil
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Parse command line arguments
parser = argparse.ArgumentParser(description='Fetch data from Google Sheets and build the website.')
parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
parser.add_argument('--backup', action='store_true', help='Create a backup of the existing Excel file')
parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching data from Google Sheets and just build the website')
parser.add_argument('--template', type=str, default="docs/index.html", help='Path to the HTML template file')
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
    except Exception as e:
        print(f"Error fetching data from Google Sheets: {e}")
        exit(1)

# Build the website
print("Building the website...")
build_cmd = [
    "python", "generate_catalog.py",
    "--input", args.output,
    "--template", args.template
]

try:
    subprocess.run(build_cmd, check=True)
    print("Successfully built the website")
except subprocess.CalledProcessError as e:
    print(f"Error building the website: {e}")
    exit(1)

print("Done!") 