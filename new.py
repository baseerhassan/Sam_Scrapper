import glob
import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import random
import time
from fake_useragent import UserAgent
import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from second_script import process_csv_and_open_sites

from selenium.common.exceptions import (
    WebDriverException, NoSuchElementException, TimeoutException,
    StaleElementReferenceException, ElementNotInteractableException
)
from selenium.webdriver.support.ui import Select
import csv
import logging
from concurrent.futures import ThreadPoolExecutor
import socket

# Custom modules (ensure these are imported correctly)
import extract_addresses
from extract_value import extract_value
from masterFileSave import TableData as TD
from defendent import extract_defendant_names,should_ignore_url
from pdf import extract_pdf_descriptions, download_pdf, extract_text_from_pdf, extract_claim_value,find_addresses
# from second_script import open_second_site
import urllib3
import extract_value

# Configure longer timeouts for DNS resolution
socket.setdefaulttimeout(30)  # 30 seconds timeout

# Configure urllib3 retry strategy
urllib3.util.retry.Retry.DEFAULT_ALLOWED_METHODS = frozenset(['GET', 'POST'])
retry_strategy = urllib3.util.Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504]
)
http = urllib3.PoolManager(
    num_pools=10,
    maxsize=10,
    retries=retry_strategy,
    timeout=urllib3.Timeout(connect=5, read=30)
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def random_sleep(min_time=3, max_time=7):
    """Sleep for a random duration between min_time and max_time seconds."""
    time.sleep(random.uniform(min_time, max_time))

def simulate_human_mouse_movements():
    """Simulate human-like mouse movements."""
    screen_width, screen_height = pyautogui.size()
    print('movement')
    for _ in range(random.randint(5, 15)):
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.5))

def simulate_page_scroll(driver):
    """Simulate human-like scrolling on the page."""
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(random.randint(3, 6)):
        scroll_position = random.randint(0, scroll_height)
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        random_sleep(2, 5)

def setup_driver_with_proxies(proxy=None):
    """Set up an undetected ChromeDriver instance with optional proxy support."""
    ua = UserAgent()
    user_agent = ua.random

    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument("--disable-popup-blocking")

    if proxy:
        options.add_argument(f'--proxy-server={proxy}')

    # driver = CustomChrome(options=options)
    driver = CustomChrome(version_main=134, options=options)
    # driver = CustomChrome(options=options)
    return driver

def open_site(driver, url):
    """Open a URL in the browser with retry logic."""
    try:
        driver.get(url)
        return True
    except WebDriverException as e:
        logging.error(f"Error opening site: {e}")
        return False

def retry_operation(operation, max_retries=3, delay=2):
    """Retry an operation in case of failure."""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    raise Exception("Max retries exceeded.")

def download_retry_with_dns(url, driver, unique_id, max_retries=3, delay=5):
    """Retry download with DNS error handling"""
    for attempt in range(max_retries):
        try:
            return download_pdf(url, driver, unique_id)
        except urllib3.exceptions.MaxRetryError as e:
            if "NameResolutionError" in str(e):
                logging.warning(f"DNS resolution failed, attempt {attempt + 1} of {max_retries}")
                time.sleep(delay)
            else:
                raise
    logging.error(f"Failed to download after {max_retries} attempts: {url}")
    return None

def process_pdf(pdf_item, record_id, driver):
    """Process a single PDF item."""
    description = pdf_item['description']
    url = pdf_item['url']
    unique_id = f"{record_id}_value" if pdf_item.get('index', 0) > 0 else record_id
    p = download_retry_with_dns(url, driver, unique_id)
    if p:
        return {"Description": description, "Path": p}
    return None

def save_data_intermediate(table_data, filename="data.csv"):
    """Save data to CSV file incrementally."""
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(table_data)
        logging.info(f"Data saved to {filename} successfully.")
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")

def process_row_with_recovery(row, driver, table_data):
    """Process a row with better error handling and recovery"""
    try:
        columns = row.find_elements(By.TAG_NAME, "td")
        if not columns:
            return False

        row_data = [column.text for column in columns]
        if len(row_data) <= 1:
            logging.warning(f"Skipping row with insufficient columns: {row_data}")
            return False

        record_id = row_data[1]
        logging.info(f"Processing record ID: {record_id}")

        for column in columns:
            if "colCaseNumber" in column.get_attribute("class"):
                try:
                    print(f'the column is {columns[2].text}')
                    title = columns[2].text
                    # Retry opening the link with explicit waits
                    max_attempts = 3
                    r = 0
                    for attempt in range(max_attempts):
                        try:
                            link = WebDriverWait(column, 10).until(
                                EC.presence_of_element_located((By.TAG_NAME, "a"))
                            )
                            url = link.get_attribute("href")
                            # title = columns[2].text
                            print(f'the text of the title {title}')
                            a = should_ignore_url(title)
                            print(f'result {a}')
                            if should_ignore_url(title):
                                logging.info(f"Ignoring title: {title} due to matched keywords.")
                                return False  # Skip processing this URL
                            link.send_keys(Keys.CONTROL + Keys.RETURN)
                            
                            # Wait for new window and switch to it
                            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
                            driver.switch_to.window(driver.window_handles[1])
                            time.sleep(5)
                            break
                        except (TimeoutException, StaleElementReferenceException) as e:
                            if attempt == max_attempts - 1:
                                raise
                            logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                            time.sleep(2)

                    # Extract defendant names with retry
                    r +=1
                    print(f'still run {r}')
                    table_xpath = '/html/body/div[2]/section/main/div[1]/div[2]/div[1]/div[2]/div/div[2]/div/div/table'
                    data = retry_operation(
                        lambda: extract_defendant_names(table_xpath, driver),
                        max_retries=3,
                        delay=2
                    )
                    # if data is None:
                    #     logging.warning("skipping this case....")
                    #     driver.switch_to.window(driver.window_handles[0])
                    #     time.sleep(4)
                    #     try:
                    #         if len(driver.window_handles) > 1:
                    #             # driver.close()
                    #             driver.switch_to.window(driver.window_handles[0])
                    #     except Exception as cleanup_error:
                    #         logging.error(f"Error during cleanup: {cleanup_error}")
                    #     print('windows cleanup')

                    #     continue
                    print('function after defendent function')
                    row_data.append(data)
                    logging.info(f"Defendant names: {data}")

                    # Extract and process PDFs with retry
                    table2_xpath = '/html/body/div[2]/section/main/div[1]/div[2]/div[1]/div[4]/div/div[2]/div/div[2]/div[1]/div/table'
                    pdf = retry_operation(
                        lambda: extract_pdf_descriptions(table2_xpath, driver),
                        max_retries=3,
                        delay=2
                    )

                    if pdf:
                        pf = []
                        for index, pdf_item in enumerate(pdf):
                            description = pdf_item['description']
                            url = pdf_item['url']
                            unique_id = f"{record_id}_value" if index > 0 else record_id
                            p = download_retry_with_dns(url, driver, unique_id)
                            if p:
                                pf.append(p)
                                logging.info(f"PDF '{description}' downloaded successfully.")
                            else:
                                logging.warning(f"Failed to download '{description}'.")
                        row_data.append(pf)
                    else:
                        pfa = []
                        row_data.append(pfa)
                        logging.warning("No PDFs found.")

                    table_data.append(row_data)
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(4)
                    return True

                except Exception as e:
                    logging.error(f"Error processing row: {e}")
                    try:
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                    except Exception as cleanup_error:
                        logging.error(f"Error during cleanup: {cleanup_error}")
                        return False 

    except Exception as e:
        logging.error(f"Error processing row: {e}")
        return False 

class CustomChrome(uc.Chrome):
    def __del__(self):
        try:
            self.quit()
        except Exception:
            pass
        
        
        
# proxy = None  
# driver = setup_driver_with_proxies(proxy)

def main():
    proxy = None  # Replace with your proxy server if needed
    driver = setup_driver_with_proxies(proxy)
    # Keywords to ignore (case-insensitive)
    with open("config.json", "r") as file:
     config = json.load(file)

    # Extract ignore_keywords
    site1 = config.get("site1", [])
    url = site1 
    filename = config.get("datafile", [])
    table_data = []

    try:
        if not open_site(driver, url):
            logging.warning("First attempt failed, retrying...")
            time.sleep(2)
            if not open_site(driver, url):
                logging.error("Second attempt failed, closing browser.")
                driver.quit()
                return

        logging.info("Site loaded successfully!")

        # Select 'Foreclosure' checkbox
        try:
            button = retry_operation(
                lambda: WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'None selected')]"))
                )
            )
            button.click()
            checkbox = retry_operation(
                lambda: driver.find_element(By.XPATH, "//li/a/label[contains(., 'Foreclosure')]/input[@type='checkbox' and @value='42']")
            )
            checkbox.click()
            button.click()
        except Exception as e:
            logging.error(f"Error selecting 'Foreclosure' checkbox: {e}")
            driver.quit()
            return

        # Set date range
        date_from = config.get("date_from", []) 
        date_to = config.get("date_to", [])
        try:
            date_from_input = retry_operation(lambda: driver.find_element(By.ID, "DateFrom"))
            date_to_input = retry_operation(lambda: driver.find_element(By.ID, "DateTo"))
            date_from_input.send_keys(date_from)
            date_to_input.send_keys(date_to)
        except Exception as e:
            logging.error(f"Error setting date range: {e}")
            driver.quit()
            return

        # Click search button
        try:
            button = retry_operation(
                lambda: WebDriverWait(driver, 130).until(
                    EC.element_to_be_clickable((By.ID, "caseSearch"))
                )
            )
            button.click()
            logging.info("Search button clicked.")
        except Exception as e:
            logging.error(f"Error clicking search button: {e}")
            driver.quit()
            return

        # Wait for table to load
        try:
            WebDriverWait(driver, 11).until(
                EC.presence_of_element_located((By.ID, "caseList"))
            )
        except TimeoutException as e:
            logging.error(f"Error waiting for table to load: {e}")
            driver.quit()
            return
        
        driver.minimize_window()

        # Select 'All' in the dropdown
        try:
            select_element = retry_operation(
                lambda: driver.find_element(By.XPATH, '//*[@id="caseList_length"]/label/select')
            )
            select = Select(select_element)
            select.select_by_visible_text('All')
        except Exception as e:
            logging.error(f"Error selecting 'All' in dropdown: {e}")
            driver.quit()
            return

        # Find the table and process rows
        try:
            table = driver.find_element(By.ID, "caseList")
            rows = table.find_elements(By.TAG_NAME, "tr")
            total_rows = len(rows)
            logging.info(f"Total rows to process: {total_rows}")

            # Process header
            header_row = rows[0]
            header_columns = header_row.find_elements(By.TAG_NAME, "th")
            header_data = [column.text.replace('#', 'No') for column in header_columns]
            header_data.append("LINK")
            table_data.append(header_data)

            # Process data rows
            for i, row in enumerate(rows[1:], 1):
                logging.info(f"Processing row {i}/{total_rows-1}")
                if process_row_with_recovery(row, driver, table_data):  # Only save if row was processed
                    save_data_intermediate(table_data, filename)
                # process_row_with_recovery(row, driver, table_data)
                # save_data_intermediate(table_data, filename)

        except Exception as e:
            logging.error(f"Error processing table data: {e}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        logging.info("Browser closed.")



def read_csv(csv_file):
            # Read CSV file and return a list of rows
            with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                return [row for row in reader]
            
 
# def write_csv(csv_file, rows):
#     # Get all unique fieldnames from all rows
#     all_fieldnames = set()
#     for row in rows:
#         all_fieldnames.update(row.keys())  # Collect all possible column names

#     all_fieldnames = list(all_fieldnames)  # Convert set to list

#     with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=all_fieldnames)
#         writer.writeheader()

#         # Ensure every row has all columns (fill missing with empty string)
#         for row in rows:
#             writer.writerow({key: row.get(key, '') for key in all_fieldnames})
           
def write_csv(csv_file, rows):
    fieldnames = rows[0].keys()  # Assuming the keys are the same for all rows
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
             
def process_pdfs_in_row(row, pdf_list):
    for pdf_file in pdf_list:
        # Process the PDF and get some data
        processed_data = extract_pdf_data(pdf_file)
        
        # Add the processed data to the row (you can change the column name)
        row['Processed Data'] = processed_data
    
    return row


def extract_pdf_data(pdf_path):
    # Process the PDF based on description
    if "value" in pdf_path:
        print(f"Processing 'Value of Real Property' PDF: {pdf_path}...")
        text = extract_text_from_pdf(pdf_path).upper()
        # print(f'text {text}')
        claim_value = extract_claim_value(text)  # Your function to extract claim value
        if claim_value:
            print(f"Claim Value Found: {claim_value}")
            return {"Claim Value": claim_value}
        else:
            print("Claim value not found in the PDF.")
            return {"Claim Value": "Not Found"}
        
    
    #else:
        #print(f"Searching address in the summons PDF: {pdf_path}...")
        #text = extract_text_from_pdf(pdf_path).upper()  # Your existing function to extract text
        
        #addresses = 'NA'   # find_addresses(text)  # My existing function to find addresses
        #print(f"Addresses found: {addresses}")
        #return {"Addresses": addresses}
    
        
def process_pdfs_in_csv(csv_file):
    # Step 1: Read the CSV data into rows
    rows = read_csv(csv_file)
    
    # Step 2: Process each row
    for row in rows:
        
        # Step 3: Get the list of PDF files from the row (from the last column)
        # pdf_list = eval(row.get(None)[0]) if row.get(None) else []
        pdf_list = eval(row.get(None)[0])  # This assumes the list of PDFs is in the second column
        print(f'pdf file is {pdf_list}')
        processed_count = 0   # Track how many PDFs were processed
        
        if not pdf_list:
            print('yakki')
            row.setdefault("Claim Value", "No pdf")
            #row.setdefault("Addresses", "")
            continue

        # Step 4: Process the PDFs in this row and update the row with extracted data
        for pdf_path in pdf_list:
            if "value" in pdf_path: 
                print(f'pdf_path : {pdf_path}')
                # Step 5: Extract data from each PDF based on the description
                updated_data = extract_pdf_data(pdf_path)
                print(f'updated_data : {updated_data}')
            
                # Add the processed data to the row
                # row['new_data'] = updated_data
                row.update(updated_data)  # Add the extracted data (like addresses or claim value)
                
        if processed_count < 2:  
            row.setdefault("Claim Value", "Not Found")
        
        # Step 6: Update the row in the list with the processed data
        rows[rows.index(row)] = row
    
    # Step 7: Write the updated rows back to the CSV
    write_csv(csv_file, rows)
    print("CSV updated successfully!")

def extract_pdf_names(rows):
    # Extract the last list (PDF names) for each row
    pdf_names = []
    for row in rows:
        # Assuming the last entry contains the PDF file names
        pdf_list = row.get(None)  # Get the value associated with the `None` key
        if pdf_list:
            # Parse the list from the string and get the PDF names
            pdf_names_in_row = eval(pdf_list[0])  # Convert string representation of the list to an actual list
            pdf_names.append(pdf_names_in_row)
    return pdf_names


def folderCreation():
    current_directory = os.getcwd()
    download_folder = os.path.join(current_directory, "Downloads")
    old_folder = os.path.join(current_directory, "Old_Down_loads")
    datafile = glob.glob(os.path.join(current_directory, "data*"))
    print(datafile)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if len(datafile) > 0:
        if os.path.exists(datafile[0]):
            os.rename(datafile[0], f"data_{timestamp}.csv")
            print("Data File renamed to OLD.")
        else:
            print("Data File does not exist.")

    # Check if the Download folder exists
    if os.path.exists(download_folder) and os.path.isdir(download_folder):
        # Rename it to OLD
        os.rename(download_folder, f"downloads_{timestamp}")
        print("Download folder renamed to OLD.")
    else:
        print("Download folder does not exist.")
    return

if __name__ == "__main__":
    try:
        print('if')
        script_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(script_dir, 'downloads')

        folderCreation()
        main()
        process_pdfs_in_csv('data.csv') # extract Calim Values
        extract_addresses.process_pdfs(folder_path) # extract addres Values


        # Added by Trae for the Claim Value. Not Working 100%
        #extract_value.process_pdfs(script_dir)
        #extract_value.process_not_found_pdfs(script_dir)
        #extract_value.merge_values_to_data(script_dir)

    except Exception as e:
        logging.error(f"Main script error: {e}")