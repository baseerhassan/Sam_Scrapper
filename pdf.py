from selenium.webdriver.common.by import By
import time
import os
import io
import requests
import re
import pytesseract
from pdf2image import convert_from_path


def extract_pdf_descriptions(table_xpath, driver):
    """
    Extracts descriptions of PDF links from a table on the new page, skipping the header row,
    and only adds descriptions containing the specific keywords.

    Args:
        driver: Selenium WebDriver instance.
        table_xpath: XPATH of the table containing PDF links.

    Returns:
        List of filtered PDF descriptions and corresponding links.
    """

    # Ensure the page has fully loaded
    time.sleep(3)  # Adjust sleep if needed to wait for the page to load completely

    # Locate the table
    try:
        table = driver.find_element(By.XPATH, table_xpath)
    except Exception as e:
        print(f"Error: Could not find table. {e}")
        return []

    # Find all rows in the table
    rows = table.find_elements(By.TAG_NAME, "tr")

    # Variables to store specific PDFs
    last_summon = None  # Store the last occurrence of "Summon"
    value_property = None  # Store the first occurrence of "Value of Real Property"

    # Start from row 1 (skip the header row)
    for row in rows[1:]:  # Skip the first row (header row)
        cells = row.find_elements(By.TAG_NAME, "td")  # Find all columns in the row
        if len(cells) >= 2:  # Ensure at least two columns exist
            try:
                link_element = cells[1].find_element(By.TAG_NAME, "a")  # The link is in the second column
            except Exception as e:
                print(f"No <a> element found in row: {row}")
                continue

            pdf_description = link_element.text.strip()  # Extract the description (text of the link)
            pdf_url = link_element.get_attribute("href")  # Extract the href (PDF URL)

            # Check if the description contains "Summon" (case-insensitive)
            if "summon" in pdf_description.lower():
                last_summon = {"description": pdf_description, "url": pdf_url}  # Keep replacing to get the last one

            # Check if the description contains "Value of Real Property" (case-insensitive)
            if "value of real property" in pdf_description.lower() and value_property is None:
                value_property = {"description": pdf_description, "url": pdf_url}  # Store first occurrence

    # Ensure Summon is first and Value of Real Property is second
    pdf_details = []
    if last_summon:
        pdf_details.append(last_summon)
    if value_property:
        pdf_details.append(value_property)

    print(f"Filtered PDF Descriptions and URLs: {pdf_details}")
    return pdf_details



from selenium import webdriver

def download_pdf(pdf_url, driver, record_id, download_folder="downloads"):
    """
    Downloads a PDF from the provided URL using Selenium session cookies and saves it locally.

    Args:
        pdf_url (str): The URL of the PDF to download.
        driver (webdriver): Selenium WebDriver instance with an active session.
        record_id (str): Unique record ID to name the PDF file.
        download_folder (str): The folder where the PDF should be saved.

    Returns:
        str: Path to the downloaded PDF file, or None if the download fails.
    """
    
    # Ensure the download folder exists
    os.makedirs(download_folder, exist_ok=True)

    # Generate a meaningful filename using the record ID
    pdf_name = f"{record_id}.pdf"  # Example: "2025-CC-001974-O.pdf"
    pdf_path = os.path.join(download_folder, pdf_name)

    # Get cookies from Selenium session and set them in the requests session
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', ''), path=cookie.get('path', '/'))

    # Download the PDF using requests with session cookies
    response = session.get(pdf_url, stream=True)
    if response.status_code == 200:
        with open(pdf_path, "wb") as pdf_file:
            for chunk in response.iter_content(chunk_size=1024):
                pdf_file.write(chunk)
        print(f"Downloaded: {pdf_path}")
        return pdf_path
    else:
        print(f"Failed to download: {pdf_url} (Status Code: {response.status_code})")
        return None

import fitz
import pytesseract
from PIL import Image
import re



def extract_text_from_pdf(pdf_path):
    # Check if "value" is present in the filename
    if "value" in pdf_path:
        print('2 pages ')
        start_page, end_page = 1, 2  # Process the first two pages
    else:
        print('1 page')
        start_page, end_page = 1, 1  # Process only the first page

    # Convert the specified pages of the PDF to images
    images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)
    
    extracted_text = ""
    for img in images:
        # Perform OCR on each page image and append the text
        extracted_text += pytesseract.image_to_string(img) + "\n"
    
    return extracted_text


import pyap

import re

def find_addresses(text, country='US'):
    # Parse the text to find addresses
    addresses = pyap.parse(text, country=country)
    print(addresses)
    
    # Return the first address if any are found
    return str(addresses[0]) if addresses else None

def convert_to_float(value_str):
    """Convert string value to float, removing commas and dollar signs"""
    if value_str:
        # Remove $ and , then convert to float
        return float(value_str.replace('$', '').replace(',', ''))
    return 0.0


def extract_claim_value(text):
    """
    Extracts the total estimated value of claim from the given text, testing multiple patterns.

    Args:
        text: The text extracted from the PDF.

    Returns:
        The claim value as a string, or None if not found.
    """
    import re

    
# Preprocessing: Remove underscores and spaces within numbers
    #cleaned_text = re.sub(r'(?<=\d)[_\s](?=\d)', '', text)
    cleaned_text = re.sub(r'(?<=\d)[_\s](?=\d)', '', text)  # Fix broken numbers
    cleaned_text = re.sub(r'[_]+', '', cleaned_text)  # Remove all underscores
    print (cleaned_text )
    # Regex pattern to match dollar values appearing before or after the phrase
    patterns = [
        r"\$?\s?(\d[\d,]*\.?\d*)\s*=\s*TOTAL\s+ESTIMATED\s+VALUE\s+OF\s+CLAIM|\$?\s?(\d[\d,]*\.?\d*)\s*TOTAL\s+ESTIMATED\s+VALUE(?:\s+OF\s+CLAIM)?",
        r"\$?\s?(\d[\d,]*\.?\d*)\s+TOTAL\s+ESTIMATED\s+VALUE(?:\s+OF\s+CLAIM)?",
        r"TOTAL\s+ESTIMATED\s+VALUE(?:\s+OF\s+CLAIM)?\s+\$?\s?(\d[\d,]*\.?\d*)",
        r"\d+\.\s*TOTAL\s+ESTIMATED\s+VALUE\s+OF\s+CLAIM\s*-\s*\$?\s*(\d[\d,]*\.?\d*)",
        r"(?:TOTAL ESTIMATED VALUE OF CLAIM|Total Estimated Value of Claim:).*?[\$](\d{1,3}(?:,\d{3})*(?:\.\d{2})?|Greater than \$\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        r"TOTAL\s+ESTIMATED\s+VALUE\s+OF\s+CLAIM\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)[.\s]*TOTAL\s+ESTIMATED\s+VALUE\s+OF\s+CLAIM"
        
    
    ]
        
        # Iterate over patterns and try to find a match
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            print("Match")
            # Get all groups that actually captured something
            values = [convert_to_float(g) for g in match.groups() if g is not None]
            # Filter values greater than min_value
            print("Values are " , values)
            valid_values = [v for v in values if v > 100]
            if valid_values:
                # Return the first value that meets the criteria
                return max(valid_values)
        # If no pattern matches, return None
    return 0