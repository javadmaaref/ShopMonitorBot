"""
shop_b_scraper.py
"""

import logging
from typing import Optional
import random
import time
import requests
from bs4 import BeautifulSoup

from .utils import persian_to_english

def extract_price_from_shopB(session: requests.Session, link: str) -> Optional[float]:
    """
    Extract price from a ShopB (formerly "Torob") product page.

    Args:
        session (requests.Session): A requests session with retry logic.
        link (str): The URL of the product page on ShopB.

    Returns:
        float: The price if found, else None.
    """
    logging.info(f"Extracting price from ShopB link: {link}")
    try:
        delay = random.uniform(1, 3)
        logging.info(f"Waiting {delay:.2f} seconds before ShopB request...")
        time.sleep(delay)

        response = session.get(link, timeout=(10, 30), verify=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        price_containers = soup.find_all('div', class_='Showcase_buy_box_text__otYW_')

        if len(price_containers) >= 2:
            price_text = price_containers[1].text
            if 'تومان' in price_text:
                price_text = price_text.split('تومان')[0].strip()
                price_text = ''.join(price_text.split())
                price_str = persian_to_english(price_text)
                logging.info(f"Successfully extracted ShopB price: {price_str}")
                return float(price_str)

        logging.warning(f"Price element not found for ShopB URL: {link}")
        return None

    except Exception as e:
        logging.error(f"Error extracting ShopB price from {link}: {str(e)}")
        raise
