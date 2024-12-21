"""
shop_a_scraper.py
"""

import logging
from typing import Tuple, Optional
from bs4 import BeautifulSoup
import random
import time
import requests

from .utils import persian_to_english


def extract_shopA_info(session: requests.Session, product_id: str) -> Tuple[Optional[float], Optional[int]]:
    """
    Extract price and stock information from ShopA product page.

    Args:
        session (requests.Session): A requests session with retry logic.
        product_id (str): The product identifier from ShopA.

    Returns:
        (price, stock):
            price (float): The product price, if found.
            stock (int): 0 if out of stock, 1 if in stock, otherwise None if uncertain.
    """
    url = f"https://shopa.com/single-product.php?id={product_id}"
    logging.info(f"Extracting info from ShopA product ID: {product_id}")

    try:
        response = session.get(url, timeout=(10, 30), verify=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        stock_text = soup.find('b', class_='text-primary')
        if not stock_text:
            logging.warning(f"Stock status not found for ShopA URL: {url}")
            return None, None

        stock = 0 if 'ناموجود' in stock_text.text else 1
        logging.info(f"ShopA Stock status: {'Out of Stock' if stock == 0 else 'Available'}")

        price_element = soup.find('strong', class_='text-success font-size-large font-weight-bold mt-2')
        if price_element:
            price_text = price_element.text.strip()
            if 'تومان' in price_text:
                price_text = price_text.split('تومان')[0].strip().replace(',', '')
                price_str = persian_to_english(price_text)
                try:
                    price_float = float(price_str)
                    logging.info(f"Successfully extracted ShopA price: {price_float}")
                    return price_float, stock
                except ValueError:
                    logging.error(f"Error converting price '{price_str}' to float for URL: {url}")
                    return None, stock

        logging.warning(f"Price element not found for ShopA URL: {url}")
        return None, stock

    except Exception as e:
        logging.error(f"Error extracting ShopA info from {url}: {str(e)}")
        raise
