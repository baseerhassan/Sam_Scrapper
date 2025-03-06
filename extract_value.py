import os
import re
import csv
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def extract_text_from_pdf(pdf_path):
    try:
        # Convert PDF to images with higher DPI for better OCR quality
        images = convert_from_path(pdf_path, dpi=300)
        text = ""
        for image in images:
            # Apply image preprocessing for better OCR
            text += pytesseract.image_to_string(
                image,
                config='--psm 6 --oem 3'
            )
        # Debug: Print full text content
        print("Full extracted text:\n", text)
        return text
    except Exception as e:
        print(f"Error processing {pdf_path}: {str(e)}")
        return ""

def extract_value_reprocess(text):
    # Debug: Print the text being processed
    print("Reprocessing text:\n", text[:500], "...\n")
    
    # Specific patterns for reprocessing with improved value detection
    reprocess_patterns = [
        # Primary patterns for total estimated value with exact decimal format
        r'(?i)(?:^|\n|\s)TOTAL\s+ESTIMATED\s+VALUE\s*[:=\-]?\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})\b',
        r'(?i)(?:^|\n|\s)ESTIMATED\s+TOTAL\s+VALUE\s*[:=\-]?\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})\b',
        # Enhanced numbered list patterns with flexible value formats
        r'(?im)^\s*\d+\.\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})\s*(?:Total Estimated|Amount|Value)',
        r'(?im)^\s*\d+\.\s*TOTAL\s+ESTIMATED\s+VALUE\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?im)^\s*\d+\.\s*(?:Total Estimated|Amount|Value)\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        # Value patterns with context
        r'(?i)TOTAL\s+ESTIMATED\s+VALUE\s+OF\s+CLAIM\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?i)CLAIM\s+VALUE\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?i)VALUE\s+OF\s+(?:THE\s+)?CLAIM\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        # Amount patterns with exact decimal matching
        r'(?i)TOTAL\s+(?:CLAIM\s+)?AMOUNT\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        r'(?i)AMOUNT\s+(?:OF\s+)?CLAIM\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
        # Fallback patterns with strict decimal format
        r'(?i)\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})\s*(?:Total Estimated|Amount|Value)',
        r'(?i)(?:AMOUNT|VALUE)\s*[:=\-]?\s*\$\s*(\d{1,3}(?:,\d{3})*\.\d{2})'
    ]
    
    for pattern in reprocess_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            groups = [g for g in match.groups() if g is not None]
            if groups:
                value = groups[0]
                if value.startswith('Greater than $'):
                    value = value.replace('Greater than $', '')
                try:
                    float_value = float(value.replace(',', ''))
                    if float_value > 0:  # Only return if value is greater than 0
                        return float_value
                except ValueError:
                    continue
    
    # If no match found with reprocess patterns, try the original extract_value function with improved OCR text
    value = extract_value(text)
    return value if value and value > 0 else None  # Return None instead of 0 for invalid values

def extract_value(text):
    # Debug: Print the text being processed
    print("Processing text:\n", text[:500], "...\n")
    
    # First try to find values in a numbered list format with TOTAL ESTIMATED VALUE
    numbered_list_patterns = [
        r'(?im)^\s*\d+\.\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*TOTAL\s+ESTIMATED\s+VALUE\s+OF\s+CLAIM',
        r'(?im)^\s*\d+\.\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*TOTAL\s+ESTIMATED\s+VALUE',
        r'(?im)^\s*\d+\.\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:IS\s+)?(?:THE\s+)?TOTAL\s+ESTIMATED\s+VALUE',
        r'(?im)^\s*\d+\.\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:Total\s+Estimated\s+Value|TOTAL\s+ESTIMATED\s+VALUE)'
    ]
    
    for pattern in numbered_list_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                value = match.group(1)
                return float(value.replace(',', ''))
            except (ValueError, IndexError):
                continue
    
    # If no numbered list value found, try other patterns
    patterns = [
        # Primary patterns with strong boundaries and context
        r'(?i)(?:^|\n|\s)TOTAL\s+ESTIMATED\s+VALUE\s+(?:OF\s+)?(?:CLAIM|PROPERTY|CASE)\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)(?:^|\n|\s)[$]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:IS\s+)?(?:THE\s+)?TOTAL\s+ESTIMATED\s+VALUE',
        r'(?i)TOTAL\s+ESTIMATED\s+VALUE\s*[:=\-]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        # Enhanced value patterns with variations
        r'(?i)(?:TOTAL\s+)?CLAIM\s+VALUE\s*[:=\-]?\s*(?:IS\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUE\s+OF\s+(?:THE\s+)?(?:CLAIM|PROPERTY)\s*[:=\-]?\s*(?:IS\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        # Amount patterns with improved context
        r'(?i)TOTAL\s+(?:CLAIM\s+)?AMOUNT\s*[:=\-]?\s*(?:IS\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)AMOUNT\s+(?:OF\s+)?(?:CLAIM|PROPERTY)\s*[:=\-]?\s*(?:IS\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        # Value patterns with additional context
        r'(?i)ESTIMATED\s+(?:TOTAL\s+)?VALUE\s*[:=\-]?\s*(?:IS\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL\s+(?:ESTIMATED\s+)?VALUE\s*[:=\-]?\s*(?:IS\s+)?\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        # Monetary patterns with improved matching
        r'(?i)(?:TOTAL ESTIMATED |SUM)\s+OF\s+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:Total|Value|Amount)',
        # New patterns for large monetary values
        r'(?i)\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)(?:AMOUNT|VALUE|TOTAL)\s*[:=\-]?\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)(?:^|\n|\s)\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)(?:TOTAL|CLAIM)\s+VALUE\s*[:=\-]?\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUE\s+OF\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL\s+OF\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)AMOUNT\s+OF\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)SUM\s+OF\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUED\s+AT\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ESTIMATED\s+AT\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)WORTH\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTALING\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTALS?\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)IN\s+THE\s+AMOUNT\s+OF\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)FOR\s+THE\s+SUM\s+OF\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUED\s+AT\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)APPROXIMATELY\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ABOUT\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ROUGHLY\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ESTIMATED\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)APPRAISED\s+AT\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ASSESSED\s+AT\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUED\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)WORTH\s+\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)AMOUNT:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)SUM:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ESTIMATE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)APPRAISAL:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)ASSESSMENT:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUATION:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)PRICE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)COST:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)FIGURE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)NUMBER:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)QUANTITY:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)AMOUNT\s+CLAIMED:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)CLAIMED\s+AMOUNT:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)CLAIMED\s+VALUE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUE\s+CLAIMED:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL\s+CLAIMED:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)CLAIMED\s+TOTAL:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL\s+VALUE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)VALUE\s+TOTAL:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL\s+AMOUNT:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)AMOUNT\s+TOTAL:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(?i)TOTAL\s+SUM:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        
        r'(?i)TOTAL\s+ESTIMATE:\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            groups = [g for g in match.groups() if g is not None]
            if groups:
                value = groups[0]
                try:
                    return float(value.replace(',', ''))
                except ValueError:
                    continue
    
    return None

def process_pdfs(folder_path):
    # Use downloads folder in the same directory as the script
    downloads_folder = os.path.join(folder_path, 'downloads')
    
    # Create downloads folder if it doesn't exist
    if not os.path.exists(downloads_folder):
        os.makedirs(downloads_folder)
        print(f"Created downloads folder at {downloads_folder}")
    
    # Delete existing extracted_value.csv if it exists
    output_file = os.path.join(folder_path, 'extracted_value.csv')
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted existing {output_file}")
    
    results = []
    pdf_files = [f for f in os.listdir(downloads_folder) if f.endswith('_value.pdf')]
    
    for pdf_file in pdf_files:
        case_number = pdf_file.replace('_value.pdf', '')
        pdf_path = os.path.join(downloads_folder, pdf_file)
        
        # Extract text from PDF using OCR
        print(f"Processing {pdf_file}...")
        text = extract_text_from_pdf(pdf_path)
        
        # Extract value from text
        value = extract_value(text)
        
        results.append({
            'case_number': case_number,
            'estimated_value': value if value is not None else 'Not found'
        })
    
    # Save results to CSV in the main folder
    output_file = os.path.join(folder_path, 'extracted_value.csv')
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['case_number', 'estimated_value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving results: {str(e)}")

def process_not_found_pdfs(folder_path):
    # Read the existing CSV to find 'Not found' cases
    not_found_cases = []
    csv_path = os.path.join(folder_path, 'extracted_value.csv')
    downloads_folder = os.path.join(folder_path, 'downloads')
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            not_found_cases = [row['case_number'] for row in reader 
                              if row['estimated_value'] == 'Not found']
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return
    
    if not not_found_cases:
        print("No 'Not found' cases to reprocess.")
        return
    
    print(f"Found {len(not_found_cases)} cases to reprocess...")
    
    results = []
    for case_number in not_found_cases:
        pdf_file = f"{case_number}_value.pdf"
        pdf_path = os.path.join(downloads_folder, pdf_file)
        
        if not os.path.exists(pdf_path):
            print(f"Warning: PDF file not found for case {case_number}")
            continue
        
        # Extract text from PDF using OCR
        print(f"Reprocessing {pdf_file}...")
        text = extract_text_from_pdf(pdf_path)
        
        # Extract value from text using reprocess patterns
        value = extract_value_reprocess(text)
        
        results.append({
            'case_number': case_number,
            'estimated_value': value if value is not None else 'Not found'
        })
    
    if results:
        # Read all existing entries
        existing_entries = []
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            existing_entries = list(reader)
        
        # Update existing entries with reprocessed values
        reprocessed_values = {row['case_number']: row['estimated_value'] for row in results}
        for entry in existing_entries:
            if entry['case_number'] in reprocessed_values:
                entry['estimated_value'] = reprocessed_values[entry['case_number']]
        
        # Write back all entries
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['case_number', 'estimated_value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_entries)
        
        print(f"Updated {csv_path} with reprocessed values.")
    else:
        print("\nNo results were found in the reprocessing attempt.")

def merge_values_to_data(folder_path):
    # Path to both CSV files
    extracted_value_path = os.path.join(folder_path, 'extracted_value.csv')
    data_path = os.path.join(folder_path, 'data.csv')
    
    # Check if both files exist
    if not os.path.exists(extracted_value_path):
        print("extracted_value.csv not found")
        return
    if not os.path.exists(data_path):
        print("data.csv not found")
        return
    
    try:
        # Read the extracted values
        extracted_values = {}
        with open(extracted_value_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                extracted_values[row['case_number']] = row['estimated_value']
        
        # Read and update data.csv
        rows = []
        updated = False
        with open(data_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = reader.fieldnames
            
            # Add 'Estimated Value' to headers if it doesn't exist
            if 'Estimated Value' not in headers:
                headers.append('Estimated Value')
                updated = True
            
            # Process each row
            for row in reader:
                case_number = row.get('Case Number')
                if case_number in extracted_values:
                    row['Estimated Value'] = extracted_values[case_number]
                    updated = True
                rows.append(row)
        
        # Write updated data back to data.csv if changes were made
        if updated:
            with open(data_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
            print(f"Updated {data_path} with estimated values")
        
        # Delete the extracted_value.csv file
        os.remove(extracted_value_path)
        print(f"Deleted {extracted_value_path}")
        
    except Exception as e:
        print(f"Error merging values: {str(e)}")

if __name__ == '__main__':
    folder_path = os.path.dirname(os.path.abspath(__file__))
    # Process all PDFs first
    process_pdfs(folder_path)
    # Then reprocess the 'Not found' cases
    process_not_found_pdfs(folder_path)
    # Finally, merge values to data.csv and cleanup
    merge_values_to_data(folder_path)