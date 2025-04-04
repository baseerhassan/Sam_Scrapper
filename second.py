import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from new import simulate_human_mouse_movements
import time
import csv
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random  # Add this import at the top

from fake_useragent import UserAgent
import undetected_chromedriver as uc

#New imports for handling the chromedriver errors
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import address_split


# Helper function to wait for element to be present or clickable
def wait_for_element(driver, xpath, condition=EC.presence_of_element_located, timeout=15):
    try:
        return WebDriverWait(driver, timeout).until(condition((By.XPATH, xpath)))
    except TimeoutException:  # Catch timeout error
        print(f"Element not found: {xpath}")  # Debugging log
        return None  # Return None instead of breaking execution

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
        time.sleep(2)
        input_field.send_keys(Keys.RETURN)  # Optional: Press Enter
        print(f"Entered: {address}")
        time.sleep(6)  # Wait for any page update (if required)
    except Exception as e:
        print(f"Error entering address: {e}")


def check_no_results(driver):
    """
    Checks if the 'NO RESULTS FOUND' message appears.
    If it exists, returns True (pass), otherwise False (continue execution).
    """
    try:
        element = wait_for_element(driver, '//*[@id="ngb-nav-2-panel"]/search-results/div/h2', EC.presence_of_element_located, timeout=10)
        if element.text.strip().upper() == "NO RESULTS FOUND":
            print("No results found. Skipping this address.")
            return True
    except Exception:
        pass  # If element is not found, continue execution
    
    return False


def check_multiple_results(driver):
    """
    Checks if multiple results are found in the search.
    Returns True if multiple results are detected, False otherwise.
    """
    try:
        # Look for elements that indicate multiple results
        multiple_results_xpath = '//*[@id="ngb-nav-2-panel"]/search-results/div/div/div/div[1]/h4'
        element = wait_for_element(driver, multiple_results_xpath, timeout=10)
        if "Multiple Results" in element.text:
            print("Multiple results found for this address.")
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
    time.sleep(random.uniform(1.5, 3.5))  # Random delay

    # Switch to the new tab
    driver.switch_to.window(driver.window_handles[-1])
    with open("config.json", "r") as file:
        config = json.load(file)

    # Extract site URL
    site2 = config.get("site2", [])
    # Open the second site
    driver.get(site2)
    time.sleep(random.uniform(2.0, 4.0))  # Random delay

    # Enter the property address with human-like typing
    input_field = wait_for_element(driver, '//*[@id="PropertyAddress"]', EC.visibility_of_element_located)
    input_field.clear()
    
    # Type address with random delays between characters
    for char in address:
        input_field.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes
        
    time.sleep(random.uniform(1.0, 2.0))  # Random delay before pressing Enter
    input_field.send_keys(Keys.RETURN)
    print(f"Entered address in new tab: {address}")

    time.sleep(random.uniform(3.0, 5.0))  # Random delay for page update

    # Handle potential popups or "No results found"
    try:
        if check_no_results(driver):
            print("No results found for this address.")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return None, "No results found"
        
        # Check for multiple results
        if check_multiple_results(driver):
            print("Multiple results found for this address.")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            return None, "Multiple Values"
    except Exception as e:
        print(f"Error checking results: {e}")

    return driver, "Success"  # Return both driver and status


import csv
import time


def process_csv_and_open_sites(driver, csv_file_path):
    """Reads the CSV, processes each entry, and writes extracted data back to the same CSV."""
    
    # Read CSV file into a list of dictionaries
    with open(csv_file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
            
        required_fields = [
            "Result", "Parcel ID", "Name","Property_Use_Code", "Latest_TaxYear","Assessed_Value", "Extracted Address", "Extra Data", "Total_Land_Area", "land use code",
            "Sale Date", "Beds", "Baths", "Living Area", "Gross Area", "Year Built",
            "Zoning", "Sale Amount", "Instrument #", "Book/Page", "Seller(s)", "Buyer(s)", "Deed Code",
            "image_url", "share_link"
        ]

        # Ensure required columns exist
        for field in required_fields:
            if field not in fieldnames:
                fieldnames.append(field)

        rows = list(reader)  # Read all rows at once

    for index, row in enumerate(rows):
        # Initialize a new browser for each row
        if driver is not None:
            try:
                driver.quit()
                print("Closed previous browser instance")
            except Exception as e:
                print(f"Error closing browser: {e}")
        
        print("Initializing new browser instance...")
        driver = setup_driver_with_proxies(proxy=None)
            
        case_number = row.get("Case Number", f"Row {index+1}")
        address_cell = row.get("Street", "")

        # Check if address is empty or None
        if not address_cell or address_cell.strip() == "":
            print(f"Skipping row {index + 1}: Missing address")
            row["Result"] = "Missing address"
            
            # Write the updated row back to CSV immediately
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            # Close browser before continuing to next row
            if driver is not None:
                driver.quit()
                print("Closed browser instance after missing address")
            continue

        # Process the address
        first_address = address_cell
        print(f"Processing Case {case_number}, Address: {first_address}")
        time.sleep(1)

        # Open the second site in a new tab
        driver_result = enter_property_address_in_new_tab(driver, first_address)
        time.sleep(4)
        
        # Check if we got a tuple (driver, status) or just driver
        if isinstance(driver_result, tuple):
            driver, result_status = driver_result
        else:
            driver = driver_result
            result_status = "No results found" if driver is None else "Success"
        
        if driver is None:
            print(f"{result_status} for {first_address}. Moving to next address...")
            
            # Update the row with the result status and continue to the next row
            row["Result"] = result_status
            
            # Write the updated row back to CSV immediately
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
            print(f"Updated CSV for {first_address} with '{result_status}'")
            continue  # Skip to the next row in the loop

        print("Address found, extracting data...")
        
        # Set result status to Success for successful searches
        row["Result"] = result_status
        
        try:
            # Extract data
            parcel_id, name, use_code, extracted_address, _, Latest_TaxYear, Assessed_Value = extract_data(driver)
            time.sleep(2)
            data, land, zoning, additional_data = move_to_property_section_and_get_data(driver)
            time.sleep(2)
            result = move_to_saleSection_and_get_data(driver)
            time.sleep(2)
            img_url = get_image_url(driver)
            time.sleep(2)
            share_link = click_and_get_popup_text(driver)
            time.sleep(2)
            # Initialize sale-related variables with default values
            sale_date = sale_amt = instrument = book_page = seller = buyer = deed_code = None
            
            print('we are running')
            year_built = additional_data.get("Actual Year Built", "N/A")
            beds = additional_data.get("Beds", "N/A")
            baths = additional_data.get("Baths", "N/A")
            Gross_Area = additional_data.get("Gross Area", "N/A")
            Living_Area = additional_data.get("Living Area", "N/A")
            
            print(f'the year built is {year_built} and beds is {beds} and the baths is {baths} and the gross area is {Gross_Area} and the living area is {Living_Area}')

            
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
            print("Extracted use_code:", use_code)

            # Update row with extracted data
            row["Parcel ID"] = parcel_id
            row["Name"] = name
            row["Property_Use_Code"] = use_code
            row["Extracted Address"] = extracted_address
            row["Latest_TaxYear"] = Latest_TaxYear
            row["Assessed_Value"] = Assessed_Value
            
            row["Total_Land_Area"] = data
            row["land use code"] = land
            row["Zoning"] = zoning
            
            
            row["Year Built"] = year_built
            row["Beds"] = beds
            row["Baths"] = baths
            row["Gross Area"] = Gross_Area
            row["Living Area"] = Living_Area

            row["Sale Date"] = sale_date
            row["Sale Amount"] = sale_amt
            row["Instrument #"] = instrument
            row["Book/Page"] = book_page
            row["Seller(s)"] = seller
            row["Buyer(s)"] = buyer
            row["Deed Code"] = deed_code
            row["image_url"] = img_url
            row["share_link"] = share_link
        except Exception as e:
            print(f"Error extracting data: {e}")
            row["Result"] = "Search Manually."

        # Close the new tab and switch back
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(f"Error closing tab: {e}")

        # Write all updated data back to CSV at once
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print('Csv updated')
        
        # Close the browser after processing each row
        if driver is not None:
            try:
                driver.quit()
                print("Closed browser instance after processing row")
            except Exception as e:
                print(f"Error closing browser: {e}")
    
    # Ensure driver is closed at the end
    if driver is not None:
        try:
            driver.quit()
        except:
            pass


def extract_data(driver):
    try:
        # Wait for required elements to load and extract data
        parcel_id = wait_for_element(driver, '/html/body/app-root/body/div/div/div/parcel-search-component/div/div/div/div/div/div[4]/parcel-card-container-component/div/div/ul/li/a/b').text
    except Exception as e:
        print("Parcel ID not found:", e)
        return None, None, None, None, None, None, None  # Return 7 values with None
    time.sleep(3)
    try:
        name = wait_for_element(driver, '/html/body/app-root/body/div/div/div/parcel-search-component/div/div/div/div/div/div[4]/parcel-card-container-component/div/div/div/div/parcel-card-component/div[3]/div[1]/div[1]/div[2]/div[1]/div/span[2]').text
    except Exception as e:
        print("Name not found:", e)
        name = None  # Set to None if not found
    time.sleep(3)
    try:
        use_code = wait_for_element(driver, '/html/body/app-root/body/div/div/div/parcel-search-component/div/div/div/div/div/div[4]/parcel-card-container-component/div/div/div/div/parcel-card-component/div[3]/div[1]/div[1]/div[2]/div[3]/div/span[2]').text
    except Exception as e:
        print("use_code not found:", e)
        use_code = None  # Set to None if not found
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
        table = wait_for_element(driver, '//*[@id="accordionControl"]/div[2]/div[1]/table')
        time.sleep(2)
        
        # Fix: Check if table exists and has content properly
        if table is None or not table.is_displayed():
            print("First table not found or not displayed, trying alternative table...")
            table = wait_for_element(driver, '//*[@id="accordionControl"]/div[3]/div[1]/table')
            
        if table is None:
            print("No table found at all")
            cell_1 = cell_5 = None
        else:
            first_row = table.find_element(By.XPATH, './/tbody/tr[2]')
            
            # Extract specific cells (Example: 1st and 5th cell)
            cell_1 = first_row.find_element(By.XPATH, './td[1]').text  # 1st cell
            cell_5 = first_row.find_element(By.XPATH, './td[7]').text  # 7th cell
            print("Extracted Table Data:", cell_1, cell_5)
            
    except Exception as e:
        print("Table or specific cell data not found:", e)
        cell_1 = cell_5 = None  # Set to None if not found
        
    print(f"Parcel ID: {parcel_id}, Name: {name}, Address: {address}, Element Data: {element_data}, Cell 1: {cell_1}, Cell 5: {cell_5}")

    # Return 7 values to match the unpacking in process_csv_and_open_sites
    return parcel_id, name, use_code, address, element_data, cell_1, cell_5


#new function to find the data
def move_to_property_section_and_get_data(driver):
    print('Navigating to the Property section...')

    section_link_xpath = '//*[@id="ngb-nav-6"]'
    
    # Wait for the section link and click
    try:
        section_link = wait_for_element(driver, section_link_xpath)
        section_link.click()
    except TimeoutException:
        print("Timeout: Section link not found.")
        return None, None, None  # Adjust return values as needed
    time.sleep(3)

    # Extract previous data points
    section_data_xpath = '//*[@id="ngb-nav-6-panel"]/parcel-features-card/div/div[2]/div[2]/div[1]/span[3]'
    land_use_xpath = '//td[@data-title="Land Use Code"]'
    zoning_xpath = '//td[@data-title="Zoning"]'

    # //*[@id="no-more-tables"]/table/tbody/tr/td[2]
    
    try:
        section_data_element = wait_for_element(driver, section_data_xpath)
        section_data = section_data_element.text if section_data_element else None
    except TimeoutException:
        print("Timeout: Section data not found.")
        section_data = "N/A"

    try:
        land_use_element = wait_for_element(driver, land_use_xpath)
        land_use_text = land_use_element.text if land_use_element else None
        zoning_element = wait_for_element(driver, zoning_xpath)
        zoning_text = zoning_element.text if zoning_element else None
    except TimeoutException:
        print("Timeout: Land use code not found.")
        land_use_text = "N/A"
        zoning_text = "N/A"

    # Extract data from the deeply nested divs
    print('data finding')
    additional_info_xpath = '//*[@id="ngb-nav-6-panel"]/parcel-features-card/div/div[6]/div/div[2]/div/div'
    
    try:
        additional_info_div = wait_for_element(driver, additional_info_xpath)
        sub_divs = additional_info_div.find_elements(By.XPATH, './div') if additional_info_div else None  # Get all sub-divs inside
        
        additional_data_dict = {}
        data_list = []  # Temporary list to store extracted text

        if sub_divs: 
            for div in sub_divs:
                # Get inner nested divs
                inner_divs = div.find_elements(By.XPATH, './div')
                for inner_div in inner_divs:
                    text = inner_div.text.strip()
                    if text:
                        data_list.append(text)

            # Convert list to dictionary (assuming key-value pairs)
            for i in range(0, len(data_list) - 1, 2):  
                key = data_list[i].strip().replace(":", "")  # Remove colons for consistency
                value = data_list[i + 1].strip()
                additional_data_dict[key] = value

    except TimeoutException:
        print("Timeout: Additional info section not found.")
        additional_data_dict = {"N/A": "N/A"}

    # ✅ Now `additional_data_dict` contains the extracted key-value pairs.

    # Print extracted data
    print("Extracted Section Data:", section_data)
    print("Extracted Land Use Data:", land_use_text)
    print("Extracted Additional Data:", additional_data_dict)

    return section_data, land_use_text,zoning_text, additional_data_dict  # Return all extracted values



def move_to_saleSection_and_get_data(driver):
    print('Moving to the next section...')

    next_section_xpath = '//*[@id="ngb-nav-8"]'
    time.sleep(5)
    
    # Click on the next section
    try:
        next_section_link = wait_for_element(driver, next_section_xpath)
        next_section_link.click() if next_section_link else None
        time.sleep(9) # 9 seconds is very important time for the table to load.
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
    
# Add these imports
import random

# Add this function to modify your existing setup_driver function
def setup_driver_with_stealth():
    """
    Set up a ChromeDriver instance with enhanced stealth features.
    Returns:
        Configured WebDriver instance.
    """
    ua = UserAgent()
    user_agent = ua.random

    options = uc.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument("--disable-popup-blocking")
    
    # Additional stealth settings - compatible with undetected_chromedriver
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Try to use undetected_chromedriver
    try:
        driver = uc.Chrome(options=options)
        print("Successfully initialized stealth Chrome driver")
    except Exception as e:
        print(f"Error initializing stealth Chrome: {e}")
        
        # Try alternative approach with standard Chrome
        try:
            print("Attempting to use standard Chrome with stealth settings...")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument(f'--user-agent={user_agent}')
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Successfully initialized standard Chrome with stealth settings")
        except Exception as e2:
            print(f"Error initializing standard Chrome: {e2}")
            raise Exception("Could not initialize WebDriver")
    
    # Mask WebDriver fingerprints
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        // Override the 'webdriver' property
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        
        // Override the plugins
        Object.defineProperty(navigator, 'plugins', { 
            get: () => {
                return [
                    {
                        0: {type: "application/pdf"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    },
                    {
                        0: {type: "application/x-google-chrome-pdf"},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ];
            }
        });
        
        // Override the languages
        Object.defineProperty(navigator, 'languages', { 
            get: () => ['en-US', 'en'] 
        });
        
        // Override the platform
        Object.defineProperty(navigator, 'platform', { 
            get: () => 'Win32' 
        });
        
        // Override the hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', { 
            get: () => 8 
        });
        """
    })

    return driver









   
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
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument("--disable-popup-blocking")
    
    # Add performance-enhancing options
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--dns-prefetch-disable")
    
    # Reduce memory usage
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-sync")
    
    # Disable unnecessary services
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-notifications")

    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    print("Initializing browser with optimized settings...")
    # Use undetected_chromedriver to automatically manage the ChromeDriver path
    driver = uc.Chrome(version_main=134, options=options)  # This will use the correct version of ChromeDriver automatically
    
    # Mask WebDriver fingerprints
    # driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #     "source": """
    #     Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    #     Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    #     Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    #     """
    # })

    return driver

proxy = None  
driver = setup_driver_with_proxies(proxy)

#driver = setup_driver_with_stealth()

try:
    process_csv_and_open_sites(driver, 'data.csv')
    print("Successfully Completed Second Site. Parse Extracted Address")
    print('------------Address Split:---------- ')
    address_split.process_secondsite_csv()

except Exception as e:
    print(f"An error occurred: {e}")
