import argparse
import os
import datetime
import csv
import gspread
from utils import get_gsheet_client, DEFAULT_CREDENTIALS_PATH

def main():
    parser = argparse.ArgumentParser(description='Backup Google Sheet data to CSV.')
    parser.add_argument('--credentials', type=str, default=DEFAULT_CREDENTIALS_PATH, help='Path to Google API credentials JSON file.')
    parser.add_argument('--backup-dir', type=str, required=True, help='Directory to save the backup CSV file.')
    args = parser.parse_args()

    print("Starting monthly Google Sheet backup...")

    try:
        # --- Connect to Google Sheet ---
        _client, _spreadsheet, sheet = get_gsheet_client(args.credentials)
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