"""
log_config.py
"""

import logging
import os
from datetime import datetime

def setup_logging() -> None:
    """Set up logging configuration."""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(
                f'logs/scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            ),
            logging.StreamHandler()
        ]
    )
