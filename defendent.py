# from selenium.webdriver.common.by import By
# def extract_defendant_names(table_xpath,driver):
#     """
#     Extracts defendant names from a table while ignoring entries with specific keywords.

#     Args:
#         driver: Selenium WebDriver instance.
#         table_xpath: XPATH of the table containing defendant names.
#         output_csv: Filename to save the extracted defendant names.

#     Returns:
#         List of valid defendant names.
#     """

#     # Keywords to ignore (case-insensitive)
#     ignore_keywords = ["LLC", "LP", "Inc", "Trust", "LTD", "Estate", "Corp"]

#     # Locate the table
#     try:
#         table = driver.find_element(By.XPATH, table_xpath)
#     except Exception as e:
#         print(f"Error: Could not find table. {e}")
#         return []

#     # Find all rows in the table
#     rows = table.find_elements(By.TAG_NAME, "tr")

#     # List to store valid defendant names
#     defendant_names = []

#     for row in rows:
#         cells = row.find_elements(By.TAG_NAME, "td")  # Find all columns in the row
#         if len(cells) >= 2:  # Ensure at least two columns exist
#             name_text = cells[0].text.strip()  # First column (name)
#             role_text = cells[1].text.strip()  # Second column (role)

#             # Check if the second column contains "Defendant"
#             if "Defendant" in role_text:
#                 # Skip if name contains any ignored keyword (case-insensitive)
#                 if any(re.search(rf"\b{kw}\b", name_text, re.IGNORECASE) for kw in ignore_keywords):
#                     print(f"Skipping: {name_text}")  # Debug output
#                     continue  # Skip this entry

#                 defendant_names.append([name_text])  # Store valid names

#     # Save valid names to CSV if any found
# #     if defendant_names:
# #         with open(output_csv, "w", newline="", encoding="utf-8") as file:
# #             writer = csv.writer(file)
# #             writer.writerow(["Defendant Name"])  # CSV Header
# #             writer.writerows(defendant_names)  # Write data

# #         print(f"Defendant names saved to {output_csv}")
# #     else:
# #         print("No valid defendants found.")

#     print(f'name are {defendant_names}')
#     return defendant_names
import json
import re

def should_ignore_url(url, ignore_keywords=None):
    print('ignore function')
    if ignore_keywords is None:
        # Keywords to ignore (case-insensitive)
        with open("config.json", "r") as file:
            config = json.load(file)
        ignore_keywords = config.get("ignore_keywords", [])
        #ignore_keywords = ["LLC", "LP", "Inc", "Trust", "LTD", "Estate", "Corp"]

    # Convert to lowercase for case-insensitive matching
    url_lower = url.lower()
    ignore_keywords_lower = [kw.lower() for kw in ignore_keywords]

    # Return True if any keyword is found anywhere in the URL
    return any(keyword in url_lower for keyword in ignore_keywords_lower)

# def should_ignore_url(url, ignore_keywords=None):
#     if ignore_keywords is None:
#         ignore_keywords = ["LLC", "LP", "Inc", "Trust", "LTD", "Estate", "Corp"]
    
#     return any(keyword in url for keyword in ignore_keywords)


# def should_ignore_url(url, ignore_keywords=None):
#     if ignore_keywords is None:
#         ignore_keywords = ["LLC", "LP", "Inc", "Trust", "LTD", "Estate", "Corp"]
    
#     return any(keyword in url for keyword in ignore_keywords)



import re
from selenium.webdriver.common.by import By

def extract_defendant_names(table_xpath, driver):
    """
    Extracts defendant names from a table while ignoring entries with specific keywords.

    Args:
        driver: Selenium WebDriver instance.
        table_xpath: XPATH of the table containing defendant names.

    Returns:
        List of valid defendant names.
    """

    # Keywords to ignore (case-insensitive)
    with open("config.json", "r") as file:
     config = json.load(file)

# Extract ignore_keywords
    ignore_keywords = config.get("ignore_keywords", [])
    #ignore_keywords = ["LLC", "LP", "Inc", "Trust", "LTD", "Estate", "Corp"]

    # Locate the table
    try:
        table = driver.find_element(By.XPATH, table_xpath)
    except Exception as e:
        print(f"Error: Could not find table. {e}")
        return []

    # Find all rows in the table
    rows = table.find_elements(By.TAG_NAME, "tr")

    # List to store valid defendant names
    defendant_names = []

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")  # Find all columns in the row
        if len(cells) >= 3:  # Ensure at least three columns exist
            name_text = cells[0].text.strip()  # First column (name)
            role_text_1 = cells[1].text.strip()  # Second column
            role_text_2 = cells[2].text.strip()  # Third column

            # Check if either the second or third column contains "Defendant"
            if "Defendant" in role_text_1 or "Defendant" in role_text_2:
                # Skip if name contains any ignored keyword (case-insensitive)
                if any(re.search(rf"\b{kw}\b", name_text, re.IGNORECASE) for kw in ignore_keywords):
                    print(f"Skipping: {name_text}")  # Debug output
                    # return None
                    continue  # Skip this entry

                defendant_names.append([name_text])  # Store valid names

    print(f'Defendent Names: {defendant_names}')
    return defendant_names
