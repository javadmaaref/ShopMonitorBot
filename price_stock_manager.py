"""
price_stock_manager.py

Manages the process of updating prices and stock information in Google Sheets
using data from ShopA and ShopB, and sends Telegram notifications as needed.
"""

import logging
import time
import math
from typing import Dict, List, Tuple
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random

import gspread

from .telegram_notifier import TelegramNotificationService
from .shop_a_scraper import extract_shopA_info
from .shop_b_scraper import extract_price_from_shopB
from .google_sheets import setup_google_sheets, exponential_retry, batch_update_cells

class PriceStockManager:
    def __init__(
        self,
        credentials_path: str,
        spreadsheet_url: str,
        telegram_bot_token: str,
        user_categories: Dict[str, List[str]]
    ):
        logging.info("Initializing PriceStockManager...")
        self.credentials_path = credentials_path
        self.spreadsheet_url = spreadsheet_url
        logging.info("Creating requests session...")
        self.session = self._create_session()
        logging.info("Setting up Google Sheets connection...")
        self.sheet = setup_google_sheets(self.credentials_path, self.spreadsheet_url)
        logging.info("Initializing Telegram notifier...")
        self.telegram = TelegramNotificationService(telegram_bot_token, user_categories)
        logging.info("PriceStockManager initialization complete")

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry logic.
        """
        logging.info("Configuring requests session...")
        session = requests.Session()

        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 404]
        )

        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=10,
            pool_maxsize=10
        )

        session.mount('http://', adapter)
        session.mount('https://', adapter)

        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

        logging.info("Requests session configured successfully")
        return session

    def calculate_price_difference(self, price: float, shop_b_price: float) -> float:
        """
        Calculate percentage difference between two prices.

        Args:
            price (float): Price from ShopA.
            shop_b_price (float): Price from ShopB.

        Returns:
            float: The percentage difference, or None if cannot be calculated.
        """
        try:
            if shop_b_price == 0:
                return None
            diff = ((price - shop_b_price) / shop_b_price) * 100
            # Round up to 2 decimal places
            return math.ceil(diff * 100) / 100
        except Exception as e:
            logging.error(f"Error calculating price difference: {str(e)}")
            return None

    def send_out_of_stock_summary(self, out_of_stock_products: list) -> None:
        """
        Send a summary notification for out-of-stock products.
        """
        if len(out_of_stock_products) >= 8:
            logging.info(f"Preparing out-of-stock summary for {len(out_of_stock_products)} products")

            # Group products by category
            category_products = {}
            for product_id, title, name, category in out_of_stock_products:
                if category not in category_products:
                    category_products[category] = []
                category_products[category].append((product_id, title, name))

            # Create message for each category group
            for category, products in category_products.items():
                message = (
                    f"⚠️ <b>Out-of-Stock Alert - {category}</b> ⚠️\n\n"
                    f"<b>{len(products)} products are out of stock:</b>\n\n"
                )

                for i, (product_id, title, name) in enumerate(products, 1):
                    message += (
                        f"<b>{i}. Product Name (ID: {product_id}):</b>\n"
                        f"{name}\n\n"
                    )

                self.telegram.send_out_of_stock_message(message, [category])
                logging.info(f"Sent out-of-stock summary notification for category {category}")

    def update_prices_and_stock(self) -> None:
        """
        Update prices and stock information for all products in the 'Sheet2' worksheet.
        """
        logging.info("Starting price and stock update process...")

        try:
            worksheet = exponential_retry(lambda: self.sheet.worksheet("Sheet2"))
            logging.info("Successfully accessed Sheet2")

            all_values = exponential_retry(lambda: worksheet.get_all_values())
            if not all_values:
                logging.warning("No data found in Sheet2")
                return

            headers = all_values[0]
            logging.info("Successfully retrieved worksheet data")

            # Identify required columns
            try:
                shop_b_price_col = headers.index("ShopB_Price") + 1
                id_col = headers.index("ShopA_ID") + 1
                price_col = headers.index("ShopA_Price") + 1
                stock_col = headers.index("ShopA_Stock") + 1
                category_col = headers.index("Category") + 1
                shop_b_link_col = headers.index("ShopB_Link") + 1
                logging.info("Successfully identified all required columns in Sheet2")
            except ValueError as e:
                logging.error(f"Required column not found: {str(e)}")
                return

            data = [dict(zip(headers, row)) for row in all_values[1:]]
            total_products = len(data)
            logging.info(f"Processing {total_products} products")

            cell_updates = []
            out_of_stock_products = []

            for index, row in enumerate(data, start=2):
                logging.info(f"Processing product {index - 1}/{total_products}")

                product_id = row.get('ShopA_ID', '')
                category = row.get('Category', '')

                if not product_id or not category:
                    logging.warning(f"Skipping row {index}: Missing product ShopA_ID or category")
                    continue

                current_shop_b_price = None
                current_shop_a_price = None
                current_stock = None

                shop_b_link = row.get('ShopB_Link', '')
                if shop_b_link and shop_b_link != '-':
                    try:
                        logging.info(f"Processing ShopB data for product {product_id}")
                        shop_b_price = extract_price_from_shopB(self.session, shop_b_link)
                        if shop_b_price is not None:
                            cell_updates.append((index, shop_b_price_col, str(shop_b_price)))
                            current_shop_b_price = shop_b_price
                            logging.info(f"Product {product_id}: ShopB price = {shop_b_price}")
                    except Exception as e:
                        logging.error(f"Error processing ShopB for product {product_id}: {str(e)}")

                try:
                    logging.info(f"Processing ShopA data for product {product_id}")
                    shop_a_price, shop_a_stock = extract_shopA_info(self.session, product_id)

                    if shop_a_price is not None:
                        cell_updates.append((index, price_col, str(shop_a_price)))
                        current_shop_a_price = shop_a_price
                        logging.info(f"Product {product_id}: ShopA price = {shop_a_price}")

                    if shop_a_stock is not None:
                        cell_updates.append((index, stock_col, str(shop_a_stock)))
                        current_stock = shop_a_stock
                        logging.info(f"Product {product_id}: Stock = {shop_a_stock}")

                        if shop_a_stock == 0:
                            product_title = row.get('Title', '')
                            product_persian_name = row.get('Name', '')
                            out_of_stock_products.append(
                                (product_id, product_title, product_persian_name, category)
                            )
                            logging.info(f"Product {product_id} is out of stock")

                except Exception as e:
                    logging.error(f"Error processing ShopA for product {product_id}: {str(e)}")

                # If both prices and a stock status are available, check for large price differences
                if (current_shop_a_price is not None and
                    current_shop_b_price is not None and
                    current_stock is not None and
                    current_stock > 0):

                    diff_percentage = self.calculate_price_difference(current_shop_a_price, current_shop_b_price)
                    if diff_percentage is not None and abs(diff_percentage) > 5:
                        product_name = row.get('Title', f'Product ID: {product_id}')
                        product_persian_name = row.get('Name', '')

                        logging.info(f"Price difference alert for {product_id}: {diff_percentage}%")

                        message = (
                            f"🔔 <b>Price Difference Alert - {category}</b> 🔔\n\n"
                            f"📝 <b>Product Name:</b>\n"
                            f"{product_persian_name}\n"
                            f"🆔 <b>Product ID:</b> {product_id}\n\n"
                            f"<b>ShopA Price:</b> {current_shop_a_price:,} Toman\n"
                            f"<b>ShopB Price:</b> {current_shop_b_price:,} Toman\n"
                            f"<b>Price Difference:</b> {diff_percentage:+.2f}%\n\n"
                            f"✅ <b>Status:</b> In Stock\n"
                        )

                        exponential_retry(lambda: self.telegram.send_message(message, category))
                        logging.info(f"Sent price difference alert for product {product_id}")

            # Perform batch updates if there are changes
            if cell_updates:
                logging.info(f"Starting batch updates for {len(cell_updates)} total changes...")
                batch_update_cells(worksheet, cell_updates)
                logging.info("All batch updates completed successfully")

            # Send out-of-stock notifications
            if out_of_stock_products:
                logging.info(f"Found {len(out_of_stock_products)} out-of-stock products")
                exponential_retry(lambda: self.send_out_of_stock_summary(out_of_stock_products))

            logging.info("Price and stock update process completed successfully")

        except Exception as e:
            logging.error(f"Critical error in update_prices_and_stock: {str(e)}")
            raise
