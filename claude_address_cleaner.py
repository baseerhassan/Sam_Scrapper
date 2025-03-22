import pandas as pd
import re
import os
import sys

def clean_address(address):
    """
    Clean and extract the primary address from a text string that may contain legal notices.
    
    Args:
        address (str): The address string to clean
        
    Returns:
        str or None: The cleaned address or None if input is NaN
    """
    if pd.isna(address):
        return None
    
    # Remove any legal notices or court summons text
    legal_phrases = [
        "Notice to Defendant",
        "Each defendant is required",
        "A lawsuit has been filed",
        "Dated this",
        "Clerk of the Circuit Court",
        "Plaintiff's attorney",
        "whose address is"
    ]
    
    cleaned = address
    for phrase in legal_phrases:
        if phrase in cleaned:
            # Cut the address at the legal phrase
            cleaned = cleaned.split(phrase)[0].strip()
    
    # Find the first address with zip code pattern
    # Pattern matches:
    # - City, State ZIP format (Orlando, FL 32801)
    # - Just ZIP format (32801)
    pattern = r'(.+?(?:(?:[A-Z]{2}|[A-Za-z]+)\s+\d{5}(?:-\d{4})?))'
    match = re.search(pattern, cleaned)
    
    if match:
        first_address = match.group(1).strip()
        # Check if the address ends with a comma or other punctuation
        first_address = re.sub(r'[,;]$', '', first_address)
        return first_address
    
    # If no match found with ZIP, return the first line
    if '\n' in cleaned:
        return cleaned.split('\n')[0].strip()
    
    return cleaned.strip()


def process_csv(input_file, output_file=None, address_column='defendant_address', output_column='Clean Address'):
    """
    Process a CSV file to clean addresses and save the results.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str, optional): Path to save the output CSV file. If None, overwrites the input file.
        address_column (str, optional): Name of the column containing addresses to clean. Default is 'defendant_address'.
        output_column (str, optional): Name of the column to store cleaned addresses. Default is 'Clean Address'.
        
    Returns:
        pandas.DataFrame: The processed DataFrame with cleaned addresses
    """
    # Validate input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return None
        
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Check if address column exists
        if address_column not in df.columns:
            print(f"Error: Column '{address_column}' not found in the CSV file.")
            return None
            
        # Apply the cleaning function to each row
        df[output_column] = df[address_column].apply(clean_address)
        
        # Save the updated DataFrame back to CSV
        if output_file is None:
            output_file = input_file
            
        df.to_csv(output_file, index=False)
        print(f"Processed {len(df)} addresses and saved to '{output_file}'")
        
        return df
        
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return None


def print_sample_results(df, address_column='defendant_address', output_column='Clean Address', sample_size=10):
    """
    Print a sample of the results for verification.
    
    Args:
        df (pandas.DataFrame): The DataFrame containing the addresses
        address_column (str, optional): Name of the column containing original addresses
        output_column (str, optional): Name of the column containing cleaned addresses
        sample_size (int, optional): Number of samples to print. Default is 10.
    """
    print(f"\nSample of cleaned addresses (showing {min(sample_size, len(df))} of {len(df)} rows):")
    for i, row in df.head(sample_size).iterrows():
        original = row[address_column] if not pd.isna(row[address_column]) else "N/A"
        cleaned = row[output_column] if not pd.isna(row[output_column]) else "N/A"
        print(f"\nRow {i+1}:")
        print(f"Original: {original}")
        print(f"Cleaned: {cleaned}")


if __name__ == "__main__":
    # Check if file path is provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"Processing file: {input_file}")
        df = process_csv(input_file, output_file)
        
        if df is not None:
            print_sample_results(df, sample_size=5)
    else:
        # Default behavior for backward compatibility
        print("No input file specified. Using default 'data.csv'")
        df = process_csv('data.csv')
        
        if df is not None:
            print_sample_results(df, sample_size=5)
            
        print("\nUsage: python claude_address_cleaner.py [input_csv_file] [output_csv_file]")
        print("If output_csv_file is not provided, the input file will be overwritten.")


    