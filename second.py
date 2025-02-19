import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from new import simulate_human_mouse_movements
import time
import csv
from selenium.common.exceptions import TimeoutException

from fake_useragent import UserAgent
import undetected_chromedriver as uc

# Helper function to wait for element to be present or clickable
def wait_for_element(driver, xpath, condition=EC.presence_of_element_located, timeout=10):
    return WebDriverWait(driver, timeout).until(condition((By.XPATH, xpath)))

def enter_property_address(driver, address):
    """
    Waits for the 'PropertyAddress' input field and enters the given address.
    
    :param driver: Selenium WebDriver instance
    :param address: The address to enter into the input field
    """
    try:
        input_field = wait_for_element(driver, '//*[@id="PropertyAddress"]', EC.visibility_of_element_located)
        input_field.clear()  # Clear any existing text
        input_field.send_keys(address)
        time.sleep(4)
        input_field.send_keys(Keys.RETURN)  # Optional: Press Enter
        print(f"Entered: {address}")
        time.sleep(8)  # Wait for any page update (if required)
    except Exception as e:
        print(f"Error entering address: {e}")


def check_no_results(driver):
    """
    Checks if the 'NO RESULTS FOUND' message appears.
    If it exists, returns True (pass), otherwise False (continue execution).
    """
    try:
        element = wait_for_element(driver, '//*[@id="ngb-nav-2-panel"]/search-results/div/h2', EC.presence_of_element_located, timeout=5)
        if element.text.strip().upper() == "NO RESULTS FOUND":
            print("No results found. Skipping this address.")
            return True
    except Exception:
        pass  # If element is not found, continue execution
    
    return False



import csv
import time


def enter_property_address_in_new_tab(driver, address):
    """Open a new tab, enter the address, and return to the original tab."""
    # Open a new tab using JavaScript
    driver.execute_script("window.open('');")
    time.sleep(2)  # Wait for the new tab to open

    # Switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])  # Switch to the most recently opened tab
    with open("config.json", "r") as file:
     config = json.load(file)

    # Extract ignore_keywords
    site2 = config.get("site2", [])
    # Open the second site
    driver.get(site2)
    # simulate_human_mouse_movements()
    time.sleep(4)  # Wait for the page to load

    # Enter the property address
    input_field = wait_for_element(driver, '//*[@id="PropertyAddress"]', EC.visibility_of_element_located)
    input_field.clear()  # Clear any existing text
    input_field.send_keys(address)
    time.sleep(4)  # Wait before pressing Enter
    input_field.send_keys(Keys.RETURN)  # Optional: Press Enter to submit the search
    print(f"Entered address in new tab: {address}")

    time.sleep(7)  # Wait for any page update (if required)

    # Handle potential popups or "No results found"
    try:
        if check_no_results(driver):  # Check if "No results found" appears
            print("No results found for this address.")
            driver.close()  # Close the new tab if no results
            driver.switch_to.window(driver.window_handles[0])  # Switch back to the original tab
            return None  # No results found, return None
    except Exception as e:
        print(f"Error checking no results: {e}")

    return driver


import csv
import time


def process_csv_and_open_sites(driver, csv_file_path):
    """Reads the CSV, processes each entry, and writes extracted data back to the same CSV."""
    
    # Read CSV file into a list of dictionaries
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames

        # Ensure required columns exist
        required_fields = [
            "Result", "Parcel ID", "Name", "Extracted Address", "Extra Data", "data", "land use code",
            "Sale Date", "Sale Amount", "Instrument #", "Book/Page", "Seller(s)", "Buyer(s)", "Deed Code","image_url","share_link"
        ]

        # required_fields = ["Result", "Parcel ID", "Name", "Extracted Address", "Extra Data", "data", "land use code"]
        for field in required_fields:
            if field not in fieldnames:
                fieldnames.append(field)

        rows = list(reader)  # Read all rows at once

    for index, row in enumerate(rows):
        case_number = row["Case Number"]
        address_cell = row["Addresses"]

        if not address_cell:
            print(f"Skipping row {index + 1}: Missing address")
            row["Result"] = "Missing address"
            continue

        # Extract the first address
        address = address_cell.strip("[]").replace("'", "").replace('"', '').strip()
        first_address = address.split(",")[0].strip()

        print(f"Processing Case {case_number}, Address: {first_address}")
        time.sleep(3)

        # Open the second site in a new tab
        driver = enter_property_address_in_new_tab(driver, first_address)
        if driver is None:
            print(f"No results found for {first_address}. Reinitializing driver...")
            
            # Reinitialize WebDriver
            ua = UserAgent()
            user_agent = ua.random
            options = uc.ChromeOptions()
            options.add_argument("--incognito")
            # options.add_argument("--headless")
            options.add_argument(f'--user-agent={user_agent}')
            options.add_argument("--disable-popup-blocking")
            driver = uc.Chrome(version_main=132, options=options)

            row["Result"] = "No results found"
            continue

        print("Address found, extracting data...")

        # Extract data
        parcel_id, name, extracted_address, _, _, _ = extract_data(driver)
        time.sleep(3)
        data, land = move_to_section_and_get_data(driver)
        time.sleep(3)
        result = move_to_saleSection_and_get_data(driver)
        time.sleep(3)
        img_url = get_image_url(driver)
        time.sleep(3)
        share_link = click_and_get_popup_text(driver)
        time.sleep(3)
        # Initialize sale-related variables with default values
        sale_date = sale_amt = instrument = book_page = seller = buyer = deed_code = None

        
        if result:
            print(result)
            sale_date, sale_amt, instrument, book_page, seller, buyer, deed_code = result
            print("Sale Date:", sale_date)
            print("Sale Amount:", sale_amt)
            print("Instrument #:", instrument)
            print("Book/Page:", book_page)
            print("Seller(s):", seller)
            print("Buyer(s):", buyer)
            print("Deed Code:", deed_code)
        else:
            print("No data extracted.")

        print("Extracted parcel ID:", parcel_id)
        print("Extracted name:", name)
        print("Extracted data:", data)
        print("Extracted land:", land)

        # Update row with extracted data
        row["Parcel ID"] = parcel_id
        row["Name"] = name
        row["Extracted Address"] = extracted_address
        row["data"] = data
        row["land use code"] = land
        row["land use code"] = land
        row["Sale Date"] = sale_date
        row["Sale Amount"] = sale_amt
        row["Instrument #"] = instrument
        row["Book/Page"] = book_page
        row["Seller(s)"] = seller
        row["Buyer(s)"] = buyer
        row["Deed Code"] = deed_code
        row["image_url"] = img_url
        row["share_link"] = share_link


        # Close the new tab and switch back
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # Write all updated data back to CSV at once
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print('Csv updated')
    

    # Close the WebDriver after processing all rows
    driver.quit()

# def process_csv_and_open_sites(driver, csv_file_path):
#     """Reads the CSV, processes each entry, and writes extracted data back to the same CSV."""
#     rows = []  # List to hold the updated rows

#     with open(csv_file_path, mode='r', encoding='utf-8') as file:
#         reader = csv.DictReader(file)  # Use DictReader to read rows as dictionaries
#         print(f'the lenght of the reader is {reader}')
#         fieldnames = reader.fieldnames  # Get the existing field names from the CSV

#         if "Result" not in fieldnames:
#             fieldnames.append("Result")  # Ensure "Result" column exists
#         if "Parcel ID" not in fieldnames:
#             fieldnames.append("Parcel ID")
#         if "Name" not in fieldnames:
#             fieldnames.append("Name")
#         if "Extracted Address" not in fieldnames:
#             fieldnames.append("Extracted Address")
#         if "Extra Data" not in fieldnames:
#             fieldnames.append("Extra Data")
#         if "data" not in fieldnames:
#             fieldnames.append("data")
#         if "land use code" not in fieldnames:
#             fieldnames.append("land use code")

#         for row in reader:
#             case_number = row["Case Number"]
#             description = row["Description"]
#             address_cell = row["Addresses"]
#             print(address_cell)
            
#             if address_cell is not None:
#                 address = address_cell.strip("[]").replace("'", "").replace('"', '').strip()

#                 # Split the address at the first comma and take the first part
#                 first_address = address.split(",")[0].strip()

#                 # Ensure no extra whitespace is left
#                 first_address = first_address.strip()

#                 print(f'The first address is: {first_address}')
#             else:
#                 continue
                


#             if not first_address:
#                 print(f"Skipping row with missing address for case {case_number}.")
#                 row["Result"] = "Missing address"
#                 rows.append(row)
#                 continue

#             print(f"Processing Case: {case_number}, Address: {address}")
#             time.sleep(4)

#             # Open the second site in a new tab
#             driver = enter_property_address_in_new_tab(driver, first_address)
#             if driver is None:  # If no results were found, skip further processing for this row
#                 ua = UserAgent()
#                 user_agent = ua.random
#                 options = uc.ChromeOptions()
#                 options.add_argument("--incognito")
#                 options.add_argument("--headless")  # Run in headless mode
#                 options.add_argument(f'--user-agent={user_agent}')
#                 options.add_argument("--disable-popup-blocking")
#                 driver = uc.Chrome(version_main=132,options=options)  # 
#                 row["Result"] = "No results found"
#                 rows.append(row)  # Append the modified dictionary
#                 # Write to CSV immediately after processing this row
#                 with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
#                     writer = csv.DictWriter(file, fieldnames=fieldnames)
#                     writer.writeheader()  # Ensure only one header row is written
#                     writer.writerows(rows)  # Write all rows with updated data
#                 continue

#             print('Address found, continuing with extraction.')

#             # Extract and print data
#             parcel_id, name, address, element_data, cell_1, cell_5 = extract_data(driver)
#             data , land = move_to_section_and_get_data(driver)

#             print("Extracted parcel ID:", parcel_id)
#             print("Extracted name:", name)
#             print("Complete Address (without first span):", address)
#             print("Extracted data:", data)
#             print("Extracted land:", land)

#             # Store extracted data in the row
#             row["Parcel ID"] = parcel_id
#             row["Name"] = name
#             row["Extracted Address"] = address
#             row["data"] = data
#             row["land use code"] = land

#             rows.append(row)
            
#             with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
#                 writer = csv.DictWriter(file, fieldnames=fieldnames)
#                 if file.tell() == 0:  # Write the header only if the file is empty
#                     writer.writeheader()
#                 writer.writerow(row)  # Write only the current row


#             # Write to CSV immediately after processing this row
#             # with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
#             #     writer = csv.DictWriter(file, fieldnames=fieldnames)
#             #     writer.writeheader()  # Ensure only one header row is written
#             #     writer.writerows(rows)  # Write all rows with updated data

#             # Close the new tab after processing
#             driver.close()
#             driver.switch_to.window(driver.window_handles[0])  # Switch back to the original tab

#     # Close the driver after processing all rows
#     driver.quit()





def extract_data(driver):
    try:
        # Wait for required elements to load and extract data
        parcel_id = wait_for_element(driver, '/html/body/app-root/body/div/div/div/parcel-search-component/div/div/div/div/div/div[4]/parcel-card-container-component/div/div/ul/li/a/b').text
    except Exception as e:
        print("Parcel ID not found:", e)
        return None, None, None, None, None, None  # Return early if critical element is not found
    time.sleep(3)
    try:
        name = wait_for_element(driver, '/html/body/app-root/body/div/div/div/parcel-search-component/div/div/div/div/div/div[4]/parcel-card-container-component/div/div/div/div/parcel-card-component/div[3]/div[1]/div[1]/div[2]/div[1]/div/span[2]').text
    except Exception as e:
        print("Name not found:", e)
        name = None  # Set to None if not found
    time.sleep(3)
    try:
        # Wait for address to load and extract it

        address_div = wait_for_element(driver, '//*[@id="ngb-nav-5-panel"]/parcel-card-component/div[3]/div[1]/div[1]/div[3]/div[1]/div[1]')
        span_elements = address_div.find_elements(By.TAG_NAME, 'span')
        address = " ".join([span.text for span in span_elements[1:]])  # Skip the first span and join the rest
    except Exception as e:
        print("Address not found:", e)
        address = None  # Set to None if not found
    time.sleep(3)
    try:
        # Extract additional data
        element_data = wait_for_element(driver, '//*[@id="ngb-nav-5-panel"]/parcel-card-component/div[3]/div[1]/div[1]/div[2]/div[3]/div/span[2]').text
    except Exception as e:
        print("Additional data not found:", e)
        element_data = None  # Set to None if not found
    time.sleep(3)
    try:
        # Extract table data
        table = wait_for_element(driver, '//*[@id="accordionControl"]/div[3]/div[1]/table')
        first_row = table.find_element(By.XPATH, './/tbody/tr[2]')
        
        # Extract specific cells (Example: 1st and 5th cell)
        cell_1 = first_row.find_element(By.XPATH, './td[1]').text  # 1st cell
        cell_5 = first_row.find_element(By.XPATH, './td[5]').text  # 5th cell
        print("Extracted Table Data:", cell_1, cell_5)
    except Exception as e:
        print("Table or specific cell data not found:", e)
        cell_1 = cell_5 = None  # Set to None if not found

    return parcel_id, name, address, element_data, cell_1, cell_5




def move_to_section_and_get_data(driver):
    print('next')

    section_link_xpath = '//*[@id="ngb-nav-6"]'
    
    # Wait for the section link and click
    try:
        section_link = wait_for_element(driver, section_link_xpath)
        section_link.click()
    except TimeoutException:
        print("Timeout: Section link not found.")
        return None, None  # or handle differently if you need to skip
    time.sleep(3)
    # Wait for the section data to be visible
    section_data_xpath = '//*[@id="ngb-nav-6-panel"]/parcel-features-card/div/div[2]/div[2]/div[1]/span[3]'
    try:
        section_data_element = wait_for_element(driver, section_data_xpath)
        section_data = section_data_element.text
    except TimeoutException:
        print("Timeout: Section data not found.")
        return None, None  # or return default value
    time.sleep(3)
    # Extract data from the table
    land_use_xpath = '//td[@data-title="Land Use Code"]'
    try:
        land_use_element = wait_for_element(driver, land_use_xpath)
        land_use_text = land_use_element.text
    except TimeoutException:
        print("Timeout: Land use code not found.")
        land_use_text = "N/A"  # Handle as needed

    # Optional: Extract more data from the table
    # table_xpath = '//*[@id="no-more-tables"]/table'
    # You can uncomment this if you want to add table extraction later
    # try:
    #     table = wait_for_element(driver, table_xpath)
    #     # Process the table if needed
    # except TimeoutException:
    #     print("Timeout: Table not found.")

    # Print extracted data
    print("Extracted Section Data:", section_data)
    print("Extracted Table Data:", land_use_text)

    return section_data, land_use_text



def move_to_saleSection_and_get_data(driver):
    print('Moving to the next section...')

    next_section_xpath = '//*[@id="ngb-nav-8"]'
    time.sleep(5)
    
    # Click on the next section
    try:
        next_section_link = wait_for_element(driver, next_section_xpath)
        next_section_link.click()
        time.sleep(8)
    except TimeoutException:
        print("Timeout: Next section link not found.")
        return None  # Return None if section can't be accessed

    # Wait for the table in the new section
    table_xpath = '//*[@id="ngb-nav-8-panel"]/parcel-sales-card/div/div[1]/div/table'
    
    try:
        table = wait_for_element(driver, table_xpath)
    except TimeoutException:
        print("Timeout: Table not found in the new section.")
        return None

    # Extract the first row (excluding the header)
    try:
        rows = table.find_elements(By.TAG_NAME, "tr")
        if len(rows) < 2:
            print("No data rows found in the table.")
            return None  # Only header exists or table is empty

        first_row = rows[1]  # Get the first data row (skip header)
        cells = first_row.find_elements(By.TAG_NAME, "td")

        if len(cells) < 2:
            print("Not enough columns in the first row to extract data.")
            return None

        # Extract all columns except the last one, handling empty cells
        extracted_data = [cell.text.strip() if cell.text.strip() else "N/A" for cell in cells[:-1]]

    except NoSuchElementException:
        print("Error: Could not find table rows or cells.")
        return None

    # Print extracted data
    print("Extracted Data from First Row:", extracted_data)

    # Return as separate elements
    return tuple(extracted_data)


def get_image_url(driver):
    """
    Retrieves the URL of an image from the given XPath.
    
    :param driver: Selenium WebDriver instance
    :return: Image URL as a string, or None if not found
    """
    image_xpath = '//*[@id="ngb-nav-5-panel"]/parcel-card-component/div[3]/div[1]/div[2]/div/div/img'
    
    print("Fetching image URL...")

    try:
        image_element = wait_for_element(driver, image_xpath)  # Assuming wait_for_element is defined
        time.sleep(3)
        image_url = image_element.get_attribute("src")  # Get the image URL
        return image_url
    except TimeoutException:
        print("Timeout: Image not found.")
        return None
    
def click_and_get_popup_text(driver):
    """
    Clicks on a menu item and retrieves the text from the pop-up that appears.
    
    :param driver: Selenium WebDriver instance
    :return: Extracted text as a string, or None if not found
    """
    menu_xpath = '//*[@id="menu"]/div/div/ul/li[14]/a'
    popup_text_xpath = '/html/body/ngb-modal-window/div/div/send-link/div[2]/p[3]'

    print("Clicking on the menu item...")

    try:
        # Click on the menu item
        menu_item = wait_for_element(driver, menu_xpath)
        time.sleep(3)
        menu_item.click()
        time.sleep(3)  # Wait for the pop-up to appear (adjust time if needed)
        
        print("Fetching text from the pop-up...")
        popup_element = wait_for_element(driver, popup_text_xpath)
        popup_text = popup_element.text
        return popup_text
    except TimeoutException:
        print("Timeout: Element or pop-up not found.")
        return None
    
def setup_driver_with_proxies(proxy=None):
    """
    Set up an undetected ChromeDriver instance with optional proxy support.
    Args:
        proxy: Proxy server string (e.g., "http://username:password@proxyserver:port")
    Returns:
        Configured WebDriver instance.
    """
    ua = UserAgent()
    user_agent = ua.random

    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    # options.add_argument("--headless")
    # options.add_argument("--headless")  # Run in headless mode
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument("--disable-popup-blocking")

    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    # Use undetected_chromedriver to automatically manage the ChromeDriver path
    driver = uc.Chrome(version_main=132,options=options)  # This will use the correct version of ChromeDriver automatically
    
    # Mask WebDriver fingerprints
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """
    })

    return driver

proxy = None  
driver = setup_driver_with_proxies(proxy)

try:
    process_csv_and_open_sites(driver,'data.csv')   # Your main code here
except Exception as e:
    print(f"An error occurred: {e}")
