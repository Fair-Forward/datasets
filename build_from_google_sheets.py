#!/usr/bin/env python3
"""
Build the website from Google Sheets data.
This script fetches data from Google Sheets and then builds the website.
"""

import argparse
import os
import subprocess
import sys
from fetch_google_sheet import fetch_google_sheet

def run_command(command):
    """Run a shell command and print the output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def build_from_google_sheets(output_excel=None, credentials=None, skip_fetch=False, no_backup=False):
    """
    Fetch data from Google Sheets and build the website.
    
    Args:
        output_excel (str): Path to save the Excel file
        credentials (str): Path to the Google Sheets API credentials file
        skip_fetch (bool): Skip fetching data from Google Sheets
        no_backup (bool): Do not create a backup of the existing Excel file
    """
    # Set default values
    if output_excel is None:
        output_excel = "docs/data_catalog.xlsx"
    
    if credentials is None:
        credentials = "data_sources/google_sheets_api/service_account_JN.json"
    
    # Step 1: Fetch data from Google Sheets
    if not skip_fetch:
        print("Fetching data from Google Sheets...")
        success = fetch_google_sheet(credentials, output_excel, not no_backup)
        if not success:
            print("Failed to fetch data from Google Sheets. Aborting.")
            return False
    else:
        print("Skipping fetch from Google Sheets.")
    
    # Step 2: Generate the HTML
    print("Generating HTML...")
    try:
        subprocess.run(["python", "generate_catalog.py", "--input", output_excel], check=True)
        print("HTML generated successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating HTML: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Fetch data from Google Sheets and build the website.')
    parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
    parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching data from Google Sheets')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the existing Excel file')
    args = parser.parse_args()
    
    build_from_google_sheets(
        output_excel=args.output,
        credentials=args.credentials,
        skip_fetch=args.skip_fetch,
        no_backup=args.no_backup
    )

if __name__ == "__main__":
    sys.exit(main()) 