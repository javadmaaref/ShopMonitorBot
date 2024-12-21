"""
config.py
"""

# Google Sheets and Telegram Bot Configuration
CREDENTIALS_PATH = "path/to/your/service_account.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/EXAMPLE_SPREADSHEET_ID/edit"
TELEGRAM_BOT_TOKEN = "123456789:ABC-YourBotTokenHere"

# User categories (anonymized)
# Replace the keys (the chat_ids) with your actual Telegram chat IDs if needed.
# The lists contain the categories each user is subscribed to.
USER_CATEGORIES = {
    "111111111": ["MB", "CPU", "GPU"],              # UserA
    "222222222": ["SSD", "RAM", "POWER"],           # UserB
    "333333333": ["FAN", "CASE", "MONITOR"],        # UserC
    "444444444": ["MB", "CPU", "GPU", "SSD", "RAM"] # UserD
}

# Retry configuration for the main script
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds
