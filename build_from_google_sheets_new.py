import argparse
import os
import subprocess
import datetime
import shutil

# Parse command line arguments
parser = argparse.ArgumentParser(description='Fetch data from Google Sheets and build the website.')
parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the existing Excel file')
parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching data from Google Sheets and just build the website')
parser.add_argument('--template', type=str, default="docs/new_index.html", help='Path to the HTML template file')
args = parser.parse_args()

# Create a backup of the existing Excel file
if not args.no_backup and os.path.exists(args.output) and not args.skip_fetch:
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
    fetch_cmd = [
        "python", "fetch_google_sheet.py",
        "--output", args.output,
        "--credentials", args.credentials
    ]
    if args.no_backup:
        fetch_cmd.append("--no-backup")
    
    try:
        subprocess.run(fetch_cmd, check=True)
        print("Successfully fetched data from Google Sheets")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching data from Google Sheets: {e}")
        exit(1)

# Build the website
print("Building the website...")
build_cmd = [
    "python", "generate_catalog_new.py",
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