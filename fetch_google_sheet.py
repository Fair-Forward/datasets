import gspread
import pandas as pd
import os
import argparse
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def fetch_google_sheet(output_path="docs/data_catalog.xlsx", credentials_path="data_sources/google_sheets_api/service_account_JN.json", save_backup=True):
    """
    Fetch data from Google Sheets and save it to a local Excel file.
    
    Args:
        output_path (str): Path to save the Excel file
        credentials_path (str): Path to the Google Sheets API credentials file
        save_backup (bool): Whether to save a backup of the existing file
    
    Returns:
        pandas.DataFrame: The fetched data
    """
    # Setup credentials
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(credentials)
    except Exception as e:
        print(f"Error setting up credentials: {e}")
        return None
    
    # Extract correct spreadsheet ID and gid from full URL
    full_url = "https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=561894456#gid=561894456"
    spreadsheet_id = full_url.split('/d/')[1].split('/')[0]
    # Use the correct GID for the new database
    gid = 756053104
    
    try:
        # Connect to the spreadsheet
        spreadsheet = client.open_by_key(spreadsheet_id)
        sheet = spreadsheet.get_worksheet_by_id(int(gid))
        print(f"Successfully connected to sheet: {sheet.title}")
        
        # Get all values to inspect headers
        all_values = sheet.get_all_values()
        headers = all_values[0]
        print(f"Available headers: {headers}")
        
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
        
        # Map the new Google Sheets columns to the expected columns in the website
        # Based on the new database structure from data_reader_mockup.ipynb
        column_mapping = {
            'Dataset Speaking Titles': 'Dataset',
            'Country Team': 'Country/Region',
            'Domain/SDG': 'SDG/Domain',
            'Description - What can be done with this? What is this about?': 'Description and How to Use it',
            'Point of Contact/Communities': 'Author/Community',
            'Dataset Link': 'Link to Dataset',
            'Data Type': 'Data Type',
            'Deep Dive - How can you concretely work with this and build on this?': 'Description and How to Use it',  # Will be combined
            'Technical Domain': 'Data Type'  # Will be combined
        }
        
        # Create a new DataFrame with the expected columns
        new_df = pd.DataFrame()
        
        # Map columns and handle special cases
        for new_col, old_col in column_mapping.items():
            if old_col in new_df.columns:
                # If the column already exists, we need to combine values
                if old_col == 'Description and How to Use it' and new_col in df.columns:
                    # Combine description fields
                    new_df[old_col] = new_df[old_col].combine_first(df[new_col])
                    # For rows where both values exist, combine them with a separator
                    mask = (~new_df[old_col].isna()) & (~df[new_col].isna())
                    new_df.loc[mask, old_col] = new_df.loc[mask, old_col] + "\n\n" + df.loc[mask, new_col]
                elif old_col == 'Data Type' and new_col in df.columns:
                    # Combine Data Type with Technical Domain
                    for i, row in df.iterrows():
                        if pd.notna(row[new_col]) and i < len(new_df):
                            if pd.notna(new_df.loc[i, old_col]):
                                new_df.loc[i, old_col] = f"{new_df.loc[i, old_col]}, {row[new_col]}"
                            else:
                                new_df.loc[i, old_col] = row[new_col]
                else:
                    # For other cases, just use the new value if the old one is empty
                    new_df[old_col] = new_df[old_col].combine_first(df[new_col])
            else:
                # If the column doesn't exist yet, create it
                if new_col in df.columns:
                    new_df[old_col] = df[new_col]
        
        # Handle special case for Dataset - use OnSite Name as fallback if Dataset Speaking Titles is empty
        if 'OnSite Name' in df.columns and 'Dataset Speaking Titles' in df.columns:
            for i, row in df.iterrows():
                if pd.isna(row['Dataset Speaking Titles']) and pd.notna(row['OnSite Name']) and i < len(new_df):
                    new_df.loc[i, 'Dataset'] = row['OnSite Name']
        
        # Handle special case for Description - combine with Use Case Speaking Title if available
        if 'Use Case Speaking Title' in df.columns:
            for i, row in df.iterrows():
                if pd.notna(row['Use Case Speaking Title']) and i < len(new_df):
                    prefix = f"**Use Case:** {row['Use Case Speaking Title']}\n\n"
                    if 'Description and How to Use it' in new_df.columns and pd.notna(new_df.loc[i, 'Description and How to Use it']):
                        new_df.loc[i, 'Description and How to Use it'] = prefix + new_df.loc[i, 'Description and How to Use it']
                    else:
                        new_df.loc[i, 'Description and How to Use it'] = prefix
        
        # Ensure all expected columns exist
        expected_columns = [
            'Dataset', 
            'Description and How to Use it', 
            'Data Type', 
            'SDG/Domain', 
            'Country/Region', 
            'Author/Community', 
            'Link to Dataset'
        ]
        
        for col in expected_columns:
            if col not in new_df.columns:
                new_df[col] = ""
        
        # Clean up markdown links in Author/Community column
        if 'Author/Community' in new_df.columns:
            new_df['Author/Community'] = new_df['Author/Community'].apply(
                lambda x: x.replace('[', '').replace(']', '').replace('(', '').replace(')', '') if isinstance(x, str) else x
            )
        
        # Make a backup of the existing file if requested
        if save_backup and os.path.exists(output_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{os.path.splitext(output_path)[0]}_{timestamp}.xlsx"
            try:
                os.rename(output_path, backup_path)
                print(f"Backup created at {backup_path}")
            except Exception as e:
                print(f"Warning: Could not create backup: {e}")
        
        # Save to Excel
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to Excel
            new_df.to_excel(output_path, index=False)
            print(f"Data saved to {output_path}")
            
            # Return the DataFrame
            return new_df
        except Exception as e:
            print(f"Error saving Excel file: {e}")
            return new_df
    
    except gspread.exceptions.GSpreadException as e:
        print(f"Error reading sheet: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch data from Google Sheets and save it to a local Excel file.')
    parser.add_argument('--output', type=str, default="docs/data_catalog.xlsx", help='Path to save the Excel file')
    parser.add_argument('--credentials', type=str, default="data_sources/google_sheets_api/service_account_JN.json", help='Path to the Google Sheets API credentials file')
    parser.add_argument('--no-backup', action='store_true', help='Do not create a backup of the existing file')
    
    args = parser.parse_args()
    
    fetch_google_sheet(
        output_path=args.output,
        credentials_path=args.credentials,
        save_backup=not args.no_backup
    ) 