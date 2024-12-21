"""
google_sheets.py
"""

import logging
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Callable, Any, List, Tuple
import gspread.utils

def setup_google_sheets(credentials_path: str, spreadsheet_url: str) -> gspread.Spreadsheet:
    """
    Set up Google Sheets connection with retry logic.

    Args:
        credentials_path (str): Path to the JSON service account file.
        spreadsheet_url (str): Google Sheets URL.

    Returns:
        gspread.Spreadsheet: The connected spreadsheet object.
    """
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(spreadsheet_url)
        logging.info("Successfully connected to Google Sheets")
        return sheet
    except Exception as e:
        logging.error(f"Error setting up Google Sheets: {str(e)}")
        raise

def exponential_retry(func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper function to add exponential retry logic to any operation.

    Args:
        func (Callable): The function to execute.
        *args: Function arguments.
        **kwargs: Function keyword arguments.

    Returns:
        Any: The return value of the function.
    """
    BASE_DELAY = 2
    MAX_DELAY = 300
    current_delay = BASE_DELAY
    attempt = 1

    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = str(e)
            if "Quota exceeded" in error_message:
                wait_time = min(current_delay, MAX_DELAY)
                logging.warning(
                    f"Rate limit hit on attempt {attempt}. Waiting {wait_time} seconds before retry..."
                )
                time.sleep(wait_time)
                current_delay = min(current_delay * 2, MAX_DELAY)
                attempt += 1
            else:
                logging.error(f"Unexpected error: {error_message}")
                raise

def batch_update_cells(worksheet: gspread.Worksheet, updates: List[Tuple[int, int, str]]) -> None:
    """
    Perform batch updates on cells with exponential backoff.

    Args:
        worksheet (gspread.Worksheet): The worksheet to update.
        updates (List[Tuple[int, int, str]]): List of (row, col, value) updates.
    """
    BATCH_SIZE = 10
    BASE_DELAY = 2
    MAX_DELAY = 300

    logging.info(f"Starting batch updates for {len(updates)} cells...")

    batch_requests = []
    for row, col, value in updates:
        batch_requests.append({
            'range': gspread.utils.rowcol_to_a1(row, col),
            'values': [[value]]
        })

    total_batches = (len(batch_requests) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(batch_requests), BATCH_SIZE):
        batch = batch_requests[i:i + BATCH_SIZE]
        current_delay = BASE_DELAY
        batch_success = False
        attempt = 1
        current_batch = i // BATCH_SIZE + 1

        logging.info(f"Processing batch {current_batch}/{total_batches}")

        while not batch_success:
            try:
                worksheet.batch_update(batch)
                logging.info(f"Successfully updated batch {current_batch}/{total_batches}")
                batch_success = True
                time.sleep(BASE_DELAY)
            except Exception as e:
                error_message = str(e)
                if "Quota exceeded" in error_message:
                    wait_time = min(current_delay, MAX_DELAY)
                    logging.warning(
                        f"Rate limit hit on batch {current_batch}, attempt {attempt}. "
                        f"Waiting {wait_time} seconds before retry..."
                    )
                    time.sleep(wait_time)
                    current_delay = min(current_delay * 2, MAX_DELAY)
                    attempt += 1
                else:
                    logging.error(f"Unexpected error during batch update: {error_message}")
                    raise

    logging.info("All batch updates completed successfully")
