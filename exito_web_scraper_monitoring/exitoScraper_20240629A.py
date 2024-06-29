# Installed Libraries
# pip install beautifulsoup4==4.12.3
# pip install gspread oauth2client
# pip install gspread==6.1.2

# pip install selenium==4.18.1
# pip install pandas==1.5.3
# pip install fake-useragent==1.5.0

# Imported Libraries
import pandas as pd
import os
import json
import time
import random
import gspread
import datetime

from fake_useragent import UserAgent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException


# ============= Generic Auxiliary Functions ===========================================================================================

def generate_timestamp():
    # Get the current datetime
    now = datetime.datetime.now()

    # Format the datetime as a timestamp string
    timestamp = now.strftime("%Y-%m-%d_%H%M%S")
    
    return timestamp


def create_directory_if_not_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f">> Created folder: {directory_path}")
    else:
        print(f">> Folder already exists: {directory_path}")

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
    chrome_options.add_argument(f'user-agent={random_user_agent}')
    # chrome_options.add_argument("--window-size=1500,800")

    # Start the WebDriver and initiate a new browser session
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# ============= Processing Functions ==========================================================================================

def update_google_sheet(sheet, product_id, price, seller):
    # Find the row with the matching Product ID
    cell = sheet.find(str(product_id))
    if cell:
        # Assuming the 'Price' is in column 7 and 'Seller' is in column 8
        sheet.update_cell(cell.row, 7, price)
        sheet.update_cell(cell.row, 8, seller)
        print(f">> Updated Product ID {product_id} with Price: {price}, Seller: {seller}")

# ============= Site Scrapers ================================================================================================

def scrape_urls_list(index_urls_df, products_sheet):
    driver = setup_driver()

    scrape_batch = generate_timestamp()

    try:
        for row in index_urls_df.itertuples():
            try:
                index = getattr(row, '_1')
                url = getattr(row, 'URL')

                print(f">> Accessing URL: {url}")
                driver.get(url)
                sleep_for_random_duration(1.5, 3)
                # sleep_for_random_duration(2, 4)

            except WebDriverException as e:
                print(f">> [ERROR]: WebDriverException occurred while accessing {url}: {str(e)}")
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

                data = {
                    "index": index,
                    "scrape_batch": scrape_batch,
                    "timestamp": product_timestamp,
                    "price": price,
                    "seller": seller
                }

                print(f"[+] Batch: {scrape_batch}")
                print(f"[+] Timestamp: {product_timestamp}")
                print(f"[+] Index: {index}")
                print(f"[+] Price: {price}")
                print(f"[+] Seller: {seller}")

                print(f">> Successfully scraped data from {url}")
                update_google_sheet(products_sheet, index, price, seller) # Update the Google Sheets with the scraped data
                print("---------------------------------------------------------------------------------------------------------")

            except NoSuchElementException as e:
                print(f">> [ERROR]: NoSuchElementException: Element not found in {url}: {str(e)}")
            except TimeoutException as e:
                print(f">> [ERROR]: TimeoutException: Timeout while accessing element in {url}: {str(e)}")
            except Exception as e:
                print(f">> [ERROR]: General Exception while scraping data from {url}: {str(e)}")

    except Exception as e:
        print(f">> [ERROR]: An error occurred in the main scraping loop: {str(e)}")
    finally:
        driver.quit()   

# =============================================================================================================================

def main():

    # ---- 0. Define logging and errors folders -------------------------------
    activity_logs_folder  = os.path.join(os.getcwd(), "activity_logs")
    errors_folder  = os.path.join(os.getcwd(), "errors")


    #  ---- 1. Check if the folders exist, if not, create them ----------------
    create_directory_if_not_exists(activity_logs_folder)
    create_directory_if_not_exists(errors_folder)


    # ---- 2. Establish connection with Google Sheets -------------------------
    print(">> Establishing connection with Google Sheets ...")
    gc = gspread.oauth()
    spreadsheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/14XXObjIWzqs0u3F6r42m-H7_9Os6_UX95nLW9y9NkSY/edit?gid=0#gid=0")
    products_sheet  = spreadsheet.sheet1
    print(">> Connection established!")


    # ---- 3. Convert Google Sheets data to DataFrame -------------------------
    df = pd.DataFrame(products_sheet.get_all_records())
    columns = ['Index', 'URL']
    index_urls_df = df[columns]


    # ---- 4. Scrape list of URLs ---------------------------------------------
    scrape_urls_list(index_urls_df, products_sheet)

    
    

if __name__ == "__main__":
    main()