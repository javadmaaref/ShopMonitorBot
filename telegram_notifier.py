"""
telegram_notifier.py
"""

import logging
from typing import Dict, List
import requests

class TelegramNotificationService:
    def __init__(self, bot_token: str, user_categories: Dict[str, List[str]]):
        """
        Initialize Telegram notifier with user category preferences.

        Args:
            bot_token (str): Telegram bot token from BotFather.
            user_categories (Dict[str, List[str]]): Mapping of chat_ids to their subscribed categories.
        """
        self.bot_token = bot_token
        self.user_categories = user_categories
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        logging.info(f"Telegram notifier initialized for {len(user_categories)} recipients")

    def send_message(self, message: str, category: str) -> bool:
        """
        Send message to users who are subscribed to the given category.

        Args:
            message (str): Message to send.
            category (str): Product category.

        Returns:
            bool: True if message was sent successfully to all relevant recipients.
        """
        success = True
        for chat_id, allowed_categories in self.user_categories.items():
            if category in allowed_categories:
                try:
                    payload = {
                        'chat_id': chat_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    response = requests.post(self.base_url, data=payload)
                    response.raise_for_status()
                    logging.info(f"Message for category {category} sent successfully to chat_id: {chat_id}")
                except Exception as e:
                    logging.error(f"Failed to send Telegram message to chat_id {chat_id}: {str(e)}")
                    success = False
        return success

    def send_out_of_stock_message(self, message: str, categories: List[str]) -> bool:
        """
        Send out of stock message to users based on their category preferences.

        Args:
            message (str): Message to send.
            categories (List[str]): List of categories that the out-of-stock products belong to.

        Returns:
            bool: True if message was sent successfully to all relevant recipients.
        """
        success = True
        sent_to = set()

        for category in categories:
            for chat_id, allowed_categories in self.user_categories.items():
                if category in allowed_categories and chat_id not in sent_to:
                    try:
                        payload = {
                            'chat_id': chat_id,
                            'text': message,
                            'parse_mode': 'HTML'
                        }
                        response = requests.post(self.base_url, data=payload)
                        response.raise_for_status()
                        sent_to.add(chat_id)
                        logging.info(f"Out of stock message sent successfully to chat_id: {chat_id}")
                    except Exception as e:
                        logging.error(f"Failed to send out of stock message to chat_id {chat_id}: {str(e)}")
                        success = False
        return success
