import argparse
import os
import datetime
import gspread
import csv
from oauth2client.service_account import ServiceAccountCredentials

def main():
    parser = argparse.ArgumentParser(description='Backup Google Sheet data to CSV.')
    parser.add_argument('--credentials', type=str, required=True, help='Path to Google API credentials JSON file.')
    parser.add_argument('--backup-dir', type=str, required=True, help='Directory to save the backup CSV file.')
    parser.add_argument('--sheet-url', type=str, default="https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456", help='Full URL of the Google Sheet.')
    parser.add_argument('--gid', type=int, default=756053104, help='GID of the specific sheet tab.')
    args = parser.parse_args()

    print("Starting monthly Google Sheet backup...")

    try:
        # --- Connect to Google Sheet ---
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(args.credentials, scope)
        client = gspread.authorize(credentials)

        # Extract spreadsheet ID from URL
        try:
            spreadsheet_id = args.sheet_url.split('/d/')[1].split('/')[0]
        except IndexError:
            print(f"Error: Could not parse Spreadsheet ID from URL: {args.sheet_url}")
            exit(1)
            
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.get_worksheet_by_id(int(args.gid))
        print(f"Successfully connected to sheet: {sheet.title}")

        # --- Fetch Data ---
        all_values = sheet.get_all_values()
        if not all_values:
            print("Warning: No data found in the sheet.")
            return # Exit if sheet is empty

        print(f"Fetched {len(all_values)} rows from the sheet.")

        # --- Save Backup ---
        os.makedirs(args.backup_dir, exist_ok=True)
        # Use Year and Month for the filename
        current_month_str = datetime.datetime.now().strftime("%Y%m") 
        backup_filename = f"monthly_sheet_backup_{current_month_str}.csv"
        backup_filepath = os.path.join(args.backup_dir, backup_filename)

        try:
            with open(backup_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(all_values)
            print(f"Successfully created monthly backup: {backup_filepath}")
        except Exception as backup_e:
            print(f"Error writing backup CSV file: {backup_e}")
            exit(1)

    except gspread.exceptions.APIError as api_e:
        print(f"Google Sheets API Error: {api_e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main() 