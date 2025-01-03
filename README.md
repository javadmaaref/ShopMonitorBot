# ShopMonitorBot

This project tracks product prices and stock availability from two sources:
- **ShopA**
- **ShopB**

Then it updates the data in a Google Sheet and sends Telegram notifications under certain conditions.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
  - [1. Clone or Download](#1-clone-or-download)
  - [2. Install Dependencies](#2-install-dependencies)
  - [3. Configure Google Service Account](#3-configure-google-service-account)
  - [4. Set Up Spreadsheet Columns](#4-set-up-spreadsheet-columns)
  - [5. Configure the Bot](#5-configure-the-bot)
  - [6. Run the Bot](#6-run-the-bot)
- [How It Works](#how-it-works)
  - [Google Sheets Integration](#google-sheets-integration)
  - [Shop Scraping](#shop-scraping)
  - [Telegram Notifications](#telegram-notifications)
- [Extending the Project](#extending-the-project)
- [Testing](#testing)
- [License](#license)

---

## Overview

This Python-based project periodically checks product prices and stock information from:
1. **ShopA** (a mock name for your ShopA website),
2. **ShopB** (a mock name for your ShopB website),

and updates a Google Sheet with the latest information. It also sends alert messages to Telegram for:
- Products that go out of stock (summaries sent when 8 or more items are out of stock).
- Large price differences (exceeding 5%) between ShopA price and ShopB price.

---

## Features

1. **Google Sheets Integration**: Automatically updates product prices and stock statuses in a specified sheet.
2. **Robust Scraping with Retry**: The scraper retries on failures or rate-limit errors with exponential backoff.
3. **Telegram Notifications**: 
   - Sends alerts for large price differences.
   - Sends alerts for out-of-stock products.

---

## Architecture

```
my_project/
│
├── main.py                (Entry point)
├── telegram_notifier.py   (Sends messages via Telegram)
├── shop_a_scraper.py      (Scraper for ShopA)
├── shop_b_scraper.py      (Scraper for ShopB)
├── google_sheets.py       (Connection and batch updates to Google Sheets)
├── price_stock_manager.py (Coordinates scraping, updates, and notifications)
├── utils.py               (Utility functions)
├── log_config.py          (Sets up logging)
├── config.py              (Stores credentials and user data)
└── README.md
```

- **`main.py`**: Orchestrates retries and runs the update process.
- **`price_stock_manager.py`**: Main logic for reading/writing data and triggering alerts.
- **`shop_a_scraper.py` / `shop_b_scraper.py`**: Functions for extracting price/stock from respective shops.
- **`telegram_notifier.py`**: Manages sending messages to Telegram.
- **`google_sheets.py`**: Handles Google Sheets authorization and batch updates.
- **`utils.py`**: Small helper functions (e.g., digit conversion).
- **`log_config.py`**: Logging setup to both file and console.
- **`config.py`**: Holds constants for credentials, spreadsheets, tokens, and user categories.

---

## Setup Instructions

### 1. Clone or Download

```bash
git clone https://github.com/javadmaaref/ShopMonitorBot.git
cd ShopMonitorBot
```

### 2. Install Dependencies

Use Python 3.7+ and install required packages:

```bash
pip install -r requirements.txt
```

> **Example**: If you don't have a `requirements.txt` yet, create one with:
> ```text
> requests
> bs4
> gspread
> oauth2client
> urllib3
> ```

### 3. Configure Google Service Account

1. Create a **Service Account** from [Google Cloud Console](https://console.cloud.google.com/).
2. Download the `.json` key file and place it in your project folder.
3. In `config.py`, set `CREDENTIALS_PATH` to the path of that JSON file.
4. **Share** your target Google Sheet with the client email found in the JSON file (at least Read/Write access).

### 4. Set Up Spreadsheet Columns

In the Google Sheet’s **`Sheet2`** (or change the name in `price_stock_manager.py` if preferred), make sure you have at least these columns in row 1:

- `ShopA_ID`
- `Title` 
- `Name`
- `Category`
- `ShopA_Price`
- `ShopA_Stock`
- `ShopB_Link`
- `ShopB_Price`

*(Ordering of columns can vary, but the headers must match exactly, unless you adapt the code accordingly.)*

### 5. Configure the Bot

1. In `config.py`, set `TELEGRAM_BOT_TOKEN` to your actual Telegram bot token.
2. Add or remove entries in `USER_CATEGORIES` to specify which Telegram chat IDs receive alerts for which categories.

### 6. Run the Bot

```bash
python main.py
```

The script will:
1. Attempt to connect to Google Sheets.
2. Retrieve all products in **`Sheet2`**.
3. For each product:
   - Scrape price and stock from **ShopA** (using the product ID).
   - Scrape price from **ShopB** (using the link).
   - Update the Google Sheet with new data.
   - Send Telegram notifications if there’s a large price difference or if it goes out of stock.

---

## How It Works

### Google Sheets Integration

- Uses **gspread** and a Google **Service Account** to authenticate.
- **Exponential backoff** handles "Quota exceeded" or rate-limit issues.

### Shop Scraping

- Uses **requests** and **BeautifulSoup**.
- **Random delays** to mimic human behavior and reduce server load.
- **Exponential retry** for transient network errors.

### Telegram Notifications

- Sends HTTP POST requests to `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage`.
- Groups recipients by category preference (defined in `USER_CATEGORIES`).
- Sends out-of-stock summaries and price-difference alerts.

---

## Extending the Project

1. **Add more Shops**: Create a new scraper module (e.g., `shop_c_scraper.py`) and integrate it into `price_stock_manager.py`.
2. **Additional Sheets**: Modify `main.py` or `price_stock_manager.py` to read from multiple worksheets.
3. **Error Handling**: Expand or customize logging and exception handling.

---

## Testing

1. **Dry Run**: Test with a small Google Sheet with just a few rows.
2. **Unit Tests**: Optionally create unit tests for each scraper function (e.g., using `pytest`).
3. **Manual Testing**: Confirm in real-time that the script updates the Google Sheet and sends Telegram messages.

---

## License

This project is provided as-is. Adapt and use it according to your needs.  
Please ensure you comply with the terms of service for Telegram, Google APIs, and any shop websites you scrape.
