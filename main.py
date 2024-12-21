"""
main.py
"""

import logging
import time

from log_config import setup_logging
from price_stock_manager import PriceStockManager
from config import (
    CREDENTIALS_PATH,
    SPREADSHEET_URL,
    TELEGRAM_BOT_TOKEN,
    USER_CATEGORIES,
    MAX_RETRIES,
    RETRY_DELAY
)

def main():
    setup_logging()
    logging.info("Starting price and stock update script")
    logging.info(f"Target spreadsheet: {SPREADSHEET_URL}")

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Attempt {attempt + 1}/{MAX_RETRIES}")
            manager = PriceStockManager(CREDENTIALS_PATH, SPREADSHEET_URL, TELEGRAM_BOT_TOKEN, USER_CATEGORIES)
            manager.update_prices_and_stock()
            logging.info("Script completed successfully")
            break
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"All attempts failed. Last error: {str(e)}")
                raise

if __name__ == "__main__":
    main()
