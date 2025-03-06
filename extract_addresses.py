import os
import re
import csv
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def extract_text_from_pdf(pdf_path):
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        print(f"\nExtracted text from {pdf_path}:\n{text[:500]}...")
        return text
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return ""

# Define excluded addresses and business keywords
exclude_addresses = [
    "425 N ORANGE AVE",  # Courthouse address
    "425 NORTH ORANGE",
    "201 S ROSALIND AVE"  # Other court-related addresses
]

business_keywords = [
    "LLC", "INC", "CORP", "CORPORATION", "COMPANY", "CO.",
    "BANK", "ASSOCIATION", "TRUST", "DEPARTMENT", "DEPT"
]

def extract_address(text):
    # Look for text segments that likely contain defendant addresses
    defendant_segments = re.split(r'(?i)(?:TO:|SUMMONS|DEFENDANT[.:S]|AKA)', text)
    
    # More flexible pattern that matches addresses with or without apartment numbers
    pattern = r'\b\d+\s+[A-Za-z0-9\s,.-]+((?:UNIT|APT|SUITE|STE|#)\s*[A-Za-z0-9-]+\s+)?[A-Za-z0-9\s,.-]+(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|ALABAMA|ALASKA|ARIZONA|ARKANSAS|CALIFORNIA|COLORADO|CONNECTICUT|DELAWARE|FLORIDA|GEORGIA|HAWAII|IDAHO|ILLINOIS|INDIANA|IOWA|KANSAS|KENTUCKY|LOUISIANA|MAINE|MARYLAND|MASSACHUSETTS|MICHIGAN|MINNESOTA|MISSISSIPPI|MISSOURI|MONTANA|NEBRASKA|NEVADA|NEW HAMPSHIRE|NEW JERSEY|NEW MEXICO|NEW YORK|NORTH CAROLINA|NORTH DAKOTA|OHIO|OKLAHOMA|OREGON|PENNSYLVANIA|RHODE ISLAND|SOUTH CAROLINA|SOUTH DAKOTA|TENNESSEE|TEXAS|UTAH|VERMONT|VIRGINIA|WASHINGTON|WEST VIRGINIA|WISCONSIN|WYOMING)\s*\d{5}(?:-\d{4})?'
    
    all_addresses = []
    
    print(f"\nProcessing text length: {len(text)}")
    
    # Process each segment that might contain a defendant address
    for segment in defendant_segments[1:]:  # Skip the first segment as it's before any identifier
        segment = segment.strip()[:500]  # Look at first 500 chars of each segment
        matches = re.finditer(pattern, segment, re.IGNORECASE)
        
        for match in matches:
            address = match.group(0)
            print(f"Found potential address: {address}")
            # Clean up the address
            cleaned_address = address.replace('\n', ' ').strip()
            cleaned_address = re.sub(r'\s+', ' ', cleaned_address)
            cleaned_address = re.sub(r',\s*,', ',', cleaned_address)
            cleaned_address = re.sub(r'\s*,\s*', ', ', cleaned_address)
            
            # Skip excluded addresses
            if any(exclude_addr.lower() in cleaned_address.lower() for exclude_addr in exclude_addresses):
                continue
                
            # Skip business addresses
            if any(keyword.lower() in cleaned_address.lower() for keyword in business_keywords):
                continue
            
            # Basic validation: must start with a number and contain a ZIP code
            if re.match(r'^\d+', cleaned_address) and re.search(r'\d{5}', cleaned_address):
                all_addresses.append(cleaned_address)
                break  # Take only the first valid address in each segment
    
    # Return the first valid address found, if any
    return all_addresses[0] if all_addresses else None

def process_pdfs(folder_path):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # First read the existing CSV file into a dictionary for easy lookup
    data_file = os.path.join(script_dir, 'data.csv')
    existing_data = {}
    
    with open(data_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames
        if 'defendant_address' not in headers:
            headers.append('defendant_address')
        for row in reader:
            existing_data[row['Case Number']] = row
    
    # Process PDFs and extract addresses
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf') and not f.endswith('_value.pdf')]
    
    for pdf_file in pdf_files:
        case_number = pdf_file.replace('.pdf', '')
        if case_number in existing_data:  # Only process if case number exists in data.csv
            pdf_path = os.path.join(folder_path, pdf_file)
            
            # Extract text from PDF using OCR
            text = extract_text_from_pdf(pdf_path)
            
            # Extract address from text
            address = extract_address(text)
            
            if address:
                existing_data[case_number]['defendant_address'] = address
                print(f"Found address for {case_number}")
            else:
                print(f"No address found for {case_number}")
    
    # Write updated data back to CSV
    with open(data_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(existing_data.values())
    
    print(f"\nResults updated in {data_file}")

if __name__ == "__main__":
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Set the folder path to the downloads directory
    folder_path = os.path.join(script_dir, 'downloads')
    process_pdfs(folder_path)