#!/usr/bin/env python3
"""
Build the website from Google Sheets data.
This script fetches data from Google Sheets and then builds the website.
"""

import argparse
import os
import subprocess
import sys

def run_command(command):
    """Run a shell command and print the output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='Build the website from Google Sheets data.')
    parser.add_argument('--skip-fetch', action='store_true', help='Skip fetching data from Google Sheets')
    parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
    parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the existing file')
    parser.add_argument('--html-output', type=str, default="docs/index.html", help='Path to save the HTML file')
    
    args = parser.parse_args()
    
    # Check if the required packages are installed
    try:
        import pandas
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except ImportError:
        print("Required packages are not installed. Installing now...")
        run_command("pip install pandas openpyxl gspread oauth2client")
    
    # Fetch data from Google Sheets
    if not args.skip_fetch:
        print("Fetching data from Google Sheets...")
        from fetch_google_sheet import fetch_google_sheet
        df = fetch_google_sheet(
            output_path=args.output,
            credentials_path=args.credentials,
            save_backup=not args.no_backup
        )
        if df is None:
            print("Error fetching data from Google Sheets. Exiting.")
            return 1
    
    # Generate the website
    print("Generating the website...")
    result = run_command(f"python generate_catalog.py --input {args.output} --output {args.html_output}")
    if result != 0:
        print("Error generating the website. Exiting.")
        return 1
    
    print("Website built successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 