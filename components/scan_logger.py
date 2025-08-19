# components/scan_logger.py
import csv
import os
import pandas as pd # Use pandas for easier CSV manipulation

try:
    # Try importing utils to get the filename, handle potential ImportError
    import utils
    SCAN_HISTORY_FILE = utils.SCAN_HISTORY_FILE
except ImportError:
    print("Warning: Could not import utils in scan_logger.py. Using default filename.")
    SCAN_HISTORY_FILE = "scan_history.csv" # Fallback filename

# Define expected header fields
FIELDNAMES = ['Timestamp', 'Severity', 'Reasons', 'ImagePath', 'OCRText']

def _ensure_csv_exists():
    """Creates the CSV file with headers if it doesn't exist."""
    if not os.path.isfile(SCAN_HISTORY_FILE):
        try:
            print(f"'{SCAN_HISTORY_FILE}' not found. Creating file with headers.")
            # Create the directory if it doesn't exist (optional, assumes file is in current dir)
            # os.makedirs(os.path.dirname(SCAN_HISTORY_FILE), exist_ok=True)
            with open(SCAN_HISTORY_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
                writer.writeheader()
        except IOError as e:
            print(f"❌ Error creating CSV file '{SCAN_HISTORY_FILE}': {e}")
        except Exception as e:
             print(f"❌ Unexpected error creating CSV file: {e}")


def save_scan_to_csv(timestamp, severity, reasons, image_path, ocr_text):
    """Appends a new scan record to the CSV file."""
    _ensure_csv_exists() # Make sure file and headers exist
    try:
        with open(SCAN_HISTORY_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writerow({
                'Timestamp': timestamp,
                'Severity': severity,
                'Reasons': "|".join(reasons) if isinstance(reasons, list) else reasons, # Join reasons list if it's a list
                'ImagePath': image_path,
                'OCRText': ocr_text.replace('\n', '\\n') # Escape newlines for CSV compatibility
            })
        print(f"✅ Scan saved to {SCAN_HISTORY_FILE}")
    except IOError as e:
        print(f"❌ Error saving scan to CSV '{SCAN_HISTORY_FILE}': {e}")
    except Exception as e:
        print(f"❌ Unexpected error saving scan: {e}")


def load_scan_history():
    """Loads scan history from the CSV file into a list of dictionaries."""
    _ensure_csv_exists() # Make sure file exists
    history = []
    try:
        with open(SCAN_HISTORY_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Basic validation: Check if header matches expected fields
            if not reader.fieldnames or list(reader.fieldnames) != FIELDNAMES:
                 print(f"Warning: CSV header mismatch in '{SCAN_HISTORY_FILE}'. Expected {FIELDNAMES}, got {reader.fieldnames}. Attempting to read anyway.")
                 # If headers mismatch significantly, might need different logic or return empty
                 # For now, we try reading based on the file's headers if they exist

            for row in reader:
                 # Replace escaped newlines back for display purposes if needed elsewhere
                 # row['OCRText'] = row.get('OCRText', '').replace('\\n', '\n')
                 history.append(dict(row)) # Convert to standard dict
        print(f"Loaded {len(history)} records from {SCAN_HISTORY_FILE}")
        return history
    except FileNotFoundError:
        print(f"Error: Scan history file '{SCAN_HISTORY_FILE}' not found during load.")
        return []
    except Exception as e:
        print(f"Error loading scan history from CSV: {e}")
        return []


def delete_scan_history_item(timestamp_to_delete):
    """Deletes a specific scan record identified by its timestamp using pandas."""
    _ensure_csv_exists()
    if not os.path.exists(SCAN_HISTORY_FILE):
         print(f"Error: Cannot delete, file not found: {SCAN_HISTORY_FILE}")
         return False

    try:
        # Read the CSV into a pandas DataFrame
        df = pd.read_csv(SCAN_HISTORY_FILE, dtype=str) # Read all as string initially

        # Check if the timestamp exists before attempting deletion
        if timestamp_to_delete not in df['Timestamp'].values:
            print(f"Error: Timestamp '{timestamp_to_delete}' not found in scan history.")
            return False

        # Remove the row(s) with the matching timestamp
        df_filtered = df[df['Timestamp'] != timestamp_to_delete]

        # Write the modified DataFrame back to the CSV, overwriting the original
        df_filtered.to_csv(SCAN_HISTORY_FILE, index=False, encoding='utf-8')

        print(f"Successfully deleted record(s) with timestamp: {timestamp_to_delete}")
        return True

    except pd.errors.EmptyDataError:
         print(f"Warning: Scan history file '{SCAN_HISTORY_FILE}' is empty. Nothing to delete.")
         return False # Or True, depending on desired behavior for empty file
    except KeyError:
         print(f"Error: 'Timestamp' column not found in '{SCAN_HISTORY_FILE}'. Cannot delete.")
         return False
    except Exception as e:
        print(f"Error deleting record with timestamp '{timestamp_to_delete}': {e}")
        return False

# Example usage (optional, for testing this module directly)
if __name__ == "__main__":
    print("Testing scan_logger...")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_scan_to_csv(ts, "TestSeverity", ["ReasonA", "ReasonB"], "test/path.png", "Test OCR Text\nWith newline.")
    history = load_scan_history()
    print("\nCurrent History:")
    for record in history[-2:]: # Print last 2 records
        print(record)

    # Test deletion (use the timestamp just added)
    # print(f"\nAttempting to delete record with timestamp: {ts}")
    # delete_scan_history_item(ts)
    # history_after_delete = load_scan_history()
    # print("\nHistory after delete attempt:")
    # for record in history_after_delete[-2:]:
    #      print(record)
