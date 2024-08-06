# Installed Libraries
# pip install beautifulsoup4==4.12.3
# pip install gspread oauth2client
# pip install gspread==6.1.2

# pip install selenium==4.18.1
# pip install pandas==1.5.3
# pip install fake-useragent==1.5.0
# pip install numpy==1.24.2

# Imported Libraries
import os
import time
import random
import gspread
import pandas as pd
from datetime import datetime

import logging
from logging.handlers import RotatingFileHandler

from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException

from gspread.exceptions import APIError

# ============= Generic Auxiliary Functions ===========================================================================================

def generate_timestamp():
    # Get the current datetime
    now = datetime.now()

    # Format the datetime as a timestamp string
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    return timestamp


def create_directory_if_not_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f">> Created folder: {directory_path}")
    else:
        print(f">> Folder already exists: {directory_path}")

def convert_price_to_number(price):
    price_part = price.split(" ")[1].strip()
    cleaned_price = price_part.replace(".", "")
    numeric_price = int(cleaned_price)
    return numeric_price

# ============= Request Functions ===========================================================================================
   
def sleep_for_random_duration(min_duration=3, max_duration=6):
    sleep_duration = random.uniform(min_duration, max_duration)
    print(f">> Sleeping for {sleep_duration:.2f} seconds...")
    time.sleep(sleep_duration)

# ============= Setup Functions ===============================================================================================

def setup_driver():
    ua = UserAgent()
    random_user_agent = ua.random

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(f'user-agent={random_user_agent}')

    # Start the WebDriver and initiate a new browser session
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ============= Processing Functions ==========================================================================================

def update_google_sheet(sheet, product_id, price, seller, timestamp):
    # Find the row with the matching Product ID
    cell = sheet.find(str(product_id))
    if cell:
        sheet.update_cell(cell.row, 7, timestamp)
        sheet.update_cell(cell.row, 9, convert_price_to_number(price))
        sheet.update_cell(cell.row, 8, seller)
        print(f">> Updated Product ID {product_id} with Price: {price}, Seller: {seller}")

def update_historical_record(historical_sheet, updates):
    df = pd.DataFrame(historical_sheet.get_all_records())
    
    # First insertion into historical record
    if df.empty:
        update_range = 'A2:C{}'.format(len(updates) + 1)
        historical_sheet.update(update_range, updates)
        
    # Add more data into historical record
    else:
        last_empty_row = len(df.index) + 1 + 1 # plus one next empty line, plus one consider header row
        updated_sheet_height = last_empty_row + len(updates)
        new_update_range = 'A{}:C{}'.format(last_empty_row, updated_sheet_height)
        historical_sheet.update(new_update_range, updates)

# ============= Site Scrapers ================================================================================================

def scrape_urls_list(index_urls_df, products_sheet, historical_record_sheet):
    driver = setup_driver()

    updates = []

    try:
        for row in index_urls_df.itertuples():
            try:
                index = getattr(row, '_1')
                url = getattr(row, 'URL')

                print(f">> Accessing URL: {url}")
                driver.get(url)
                sleep_for_random_duration(0.8, 2.3)

            except WebDriverException as e:
                print(f">> [ERROR]: WebDriverException occurred while accessing {url}: {str(e)}")
                logger.error(str(e))
                continue

            try:
                product_timestamp = generate_timestamp()

                # Scraping logic
                price_elem = driver.find_element(By.CLASS_NAME, 'ProductPrice_container__price__XmMWA')
                if price_elem:
                    price = price_elem.text

                seller_details_section = driver.find_element(By.CLASS_NAME, 'seller-information_fs-seller-information__3otO1')
                if seller_details_section:
                    seller_content_div = seller_details_section.find_element(By.CSS_SELECTOR, 'div[data-fs-product-details-seller__content="true"]')
                    if seller_content_div:
                        inner_seller_content_div = seller_content_div.find_element(By.TAG_NAME, 'div')
                        if inner_seller_content_div:
                            seller = inner_seller_content_div.text

                # Print through console
                print(f"[+] Timestamp: {product_timestamp}")
                print(f"[+] Index: {index}")
                print(f"[+] Price: {price}")
                print(f"[+] Seller: {seller}")
                print(f">> Successfully scraped data from {url}")

                # Add scraped data to list of updates
                updates.append([product_timestamp, seller, price])
                print("---------------------------------------------------------------------------------------------------------")


                # Update the Google Sheets with the scraped data
                try:
                    update_google_sheet(products_sheet, index, price, seller, product_timestamp)
                except APIError as e:
                    if 'quota' in str(e).lower():
                        print(f">> [ERROR]: APIError: Quota exceeded.")
                        logger.error(str(e))
                    else:
                        print(f">> [ERROR]: APIError occurred: {str(e)}")
                        logger.error(str(e))

                print("---------------------------------------------------------------------------------------------------------")

            except NoSuchElementException as e:
                print(f">> [ERROR]: NoSuchElementException: Element not found in {url}: {str(e)}")
                logger.error(str(e))
            except TimeoutException as e:
                print(f">> [ERROR]: TimeoutException: Timeout while accessing element in {url}: {str(e)}")
                logger.error(str(e))
            except Exception as e:
                print(f">> [ERROR]: General Exception while scraping data from {url}: {str(e)}")
                logger.error(str(e))

    except Exception as e:
        print(f">> [ERROR]: An error occurred in the main scraping loop: {str(e)}")
        logger.error(str(e))
    finally:
        driver.quit()

        # [OPTIONAL] Perform historical record update
        # try:
        #    update_historical_record(historical_record_sheet, updates)

        # except APIError as e:
        #     if 'quota' in str(e).lower():
        #         print(f">> [ERROR]: APIError: Quota exceeded.")
        #     else:
        #         print(f">> [ERROR]: APIError occurred: {str(e)}")

# =============================================================================================================================

# Create a custom logger
logger = logging.getLogger(__name__)

activity_logs_folder  = os.path.join(os.path.dirname(os.getcwd()), "activity_logs")
print(activity_logs_folder)
create_directory_if_not_exists(activity_logs_folder)

# Create handlers
c_handler = logging.StreamHandler() # -> console
f_handler = RotatingFileHandler(os.path.join(activity_logs_folder, 'errors.log'), maxBytes=5*1024*1024, backupCount=10) # -> file
c_handler.setLevel(logging.DEBUG) 
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)


def main():
    iteration_timestamp = generate_timestamp()
    print(f">> Starting iteration at {iteration_timestamp}...")

    # ---- Establish connection with Google Sheets -------------------------
    print(">> Establishing connection with Google Sheets ...")
    gc = gspread.service_account()
    spreadsheet = gc.open_by_url("<INSERT_HERE_GOOGLE_SHEET_LINK>")
    products_sheet  = spreadsheet.sheet1
    historical_record_sheet = spreadsheet.get_worksheet_by_id('<INSERT_HERE_GOOGLE_SHEET_ID>')
    print(">> Connection established!")
    

    # ---- Convert Google Sheets data to DataFrame -------------------------
    df = pd.DataFrame(products_sheet.get_all_records())
    columns = ['Index', 'URL']
    index_urls_df = df[columns]


    # ---- Scrape list of URLs ---------------------------------------------
    start_time = time.time()
    scrape_urls_list(index_urls_df, products_sheet, historical_record_sheet)    
    print(f">> Execution time: {time.time() - start_time}")


if __name__ == "__main__":
    main()
