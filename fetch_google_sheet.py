import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import argparse
from datetime import datetime

def fetch_google_sheet(credentials_path, output_path, create_backup=True):
    """
    Fetch data from Google Sheet and save it to an Excel file.
    
    Args:
        credentials_path (str): Path to the Google Sheets API credentials file
        output_path (str): Path to save the Excel file
        create_backup (bool): Whether to create a backup of the existing Excel file
    """
    try:
        # Create backup of existing file if it exists
        if create_backup and os.path.exists(output_path):
            backup_path = f"{os.path.splitext(output_path)[0]}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            os.rename(output_path, backup_path)
            print(f"Created backup of existing file at {backup_path}")
        
        # Setup credentials
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
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
        
        # Create unique headers if necessary
        unique_headers = []
        header_count = {}
        for header in headers:
            if header in header_count:
                header_count[header] += 1
                unique_headers.append(f"{header}_{header_count[header]}")
            else:
                header_count[header] = 0
                unique_headers.append(header)
        
        # Get all data with unique headers
        data = sheet.get_all_records(expected_headers=unique_headers)
        df = pd.DataFrame(data)
        print(f"Data shape: {df.shape}")
        
        # Save to Excel
        df.to_excel(output_path, index=False)
        print(f"Successfully saved data to {output_path}")
        
        return True
    except Exception as e:
        print(f"Error fetching Google Sheet: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch data from Google Sheet and save it to an Excel file.')
    parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
    parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the existing Excel file')
    args = parser.parse_args()
    
    fetch_google_sheet(args.credentials, args.output, not args.no_backup) 