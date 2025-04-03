import pandas as pd
import re

def parse_address(address):
    """
    Parse a US address string into components: Street, City, State, and Zip.
    
    Args:
        address (str): A US address string
        
    Returns:
        dict: Dictionary with keys 'Street', 'City', 'State', and 'Zip'
    """
    if not isinstance(address, str) or pd.isna(address) or address.strip() == '':
        return {'Street': None, 'City': None, 'State': None, 'Zip': None}
    
    try:
        # Import usaddress here to allow the function to be imported 
        # even if usaddress isn't installed yet
        import usaddress
        
        # Use usaddress library to parse the address
        tagged_address, address_type = usaddress.tag(address)
        
        # Initialize components
        street_components = []
        city = None
        state = None
        zipcode = None
        
        # Extract components based on tags
        if 'AddressNumber' in tagged_address:
            street_components.append(tagged_address['AddressNumber'])
            
        if 'StreetNamePreDirectional' in tagged_address:
            street_components.append(tagged_address['StreetNamePreDirectional'])
            
        if 'StreetName' in tagged_address:
            street_components.append(tagged_address['StreetName'])
            
        if 'StreetNamePostType' in tagged_address:
            street_components.append(tagged_address['StreetNamePostType'])
            
        if 'OccupancyType' in tagged_address:
            street_components.append(tagged_address['OccupancyType'])
            
        if 'OccupancyIdentifier' in tagged_address:
            street_components.append(tagged_address['OccupancyIdentifier'])
        
        # Additional street components
        for component in ['StreetNamePostDirectional', 'SubaddressType', 'SubaddressIdentifier',
                          'BuildingName', 'StreetNamePreModifier', 'StreetNamePostModifier']:
            if component in tagged_address:
                street_components.append(tagged_address[component])
        
        # Get city, state, zip
        if 'PlaceName' in tagged_address:
            city = tagged_address['PlaceName']
            
        if 'StateName' in tagged_address:
            state = tagged_address['StateName']
        
        if 'ZipCode' in tagged_address:
            zipcode = tagged_address['ZipCode']
        
        # Format street address
        street = ' '.join(street_components).strip()
        
        # Fallback method if usaddress fails to correctly identify components
        if not city or not state:
            # Try manual parsing
            address_parts = address.split(',')
            if len(address_parts) >= 2:
                # Last part likely contains state and zip
                last_part = address_parts[-1].strip()
                
                # Extract state and zip from last part
                state_zip_match = re.search(r'([A-Za-z]+)\s+(\d{5}(?:-\d{4})?)', last_part)
                if state_zip_match:
                    if not state:
                        state = state_zip_match.group(1)
                    if not zipcode:
                        zipcode = state_zip_match.group(2)
                
                # If we have at least 2 parts, second-to-last is likely the city
                if len(address_parts) >= 2 and not city:
                    city = address_parts[-2].strip()
        
        # Normalize state to abbreviation
        state_map = {
            'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 
            'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
            'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID', 
            'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
            'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
            'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
            'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
            'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
            'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
            'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
            'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
            'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
            'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC'
        }
        
        if state and state.upper() in state_map:
            state = state_map[state.upper()]
        
        return {'Street': street, 'City': city, 'State': state, 'Zip': zipcode}
    
    except ImportError:
        print("Warning: 'usaddress' package is not installed. Falling back to regex parser.")
        return fallback_parse_address(address)
    except Exception as e:
        print(f"Error parsing address '{address}': {str(e)}")
        return fallback_parse_address(address)

def fallback_parse_address(address):
    """
    Fallback address parser using regex when usaddress fails
    
    Args:
        address (str): A US address string
        
    Returns:
        dict: Dictionary with keys 'Street', 'City', 'State', and 'Zip'
    """
    try:
        # State name to abbreviation mapping
        state_map = {
            'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 
            'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
            'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID', 
            'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
            'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
            'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
            'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
            'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
            'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
            'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
            'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
            'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
            'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC'
        }
        
        # First, try to match the state and zip which are most predictable
        state_zip_pattern = r'([A-Za-z]+)\s+(\d{5}(?:-\d{4})?)'
        state_zip_match = re.search(state_zip_pattern, address)
        
        if state_zip_match:
            potential_state = state_zip_match.group(1)
            zipcode = state_zip_match.group(2)
            
            # Convert state name to abbreviation if necessary
            state = potential_state
            if state.upper() in state_map:
                state = state_map[state.upper()]
            
            # Split by commas to find city and street
            parts = address.split(',')
            
            if len(parts) >= 2:
                # Last part contains state and zip
                # Second to last part is likely city
                city = parts[-2].strip()
                # Everything before that is street
                if len(parts) > 2:
                    street = ','.join(parts[:-2]).strip()
                else:
                    street = parts[0].strip()
            else:
                # If there are no commas, try to extract city by looking before state
                pre_state = address[:state_zip_match.start()].strip()
                parts = pre_state.split()
                if parts:
                    city = parts[-1]
                    street = ' '.join(parts[:-1])
                else:
                    city = None
                    street = pre_state
            
            return {'Street': street, 'City': city, 'State': state, 'Zip': zipcode}
        
        # If we couldn't find state/zip pattern, return empty
        return {'Street': address, 'City': None, 'State': None, 'Zip': None}
        
    except Exception:
        # If all parsing fails, return the original as street and None for others
        return {'Street': address, 'City': None, 'State': None, 'Zip': None}

def process_csv(input_file='data.csv', output_file='data.csv', address_column='Clean Address'):
    """
    Process a CSV file to parse addresses from a specified column
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        address_column (str): Name of the column containing addresses
        
    Returns:
        pandas.DataFrame: The processed DataFrame with parsed address columns
    """
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Check if address column exists
        if address_column not in df.columns:
            raise ValueError(f"Error: '{address_column}' column not found in the CSV file.")
        
        # Apply the parser to each address
        parsed_addresses = df[address_column].apply(parse_address)
        
        # Extract the components into new columns
        df['Street'] = parsed_addresses.apply(lambda x: x['Street'])
        df['City'] = parsed_addresses.apply(lambda x: x['City'])
        df['State'] = parsed_addresses.apply(lambda x: x['State'])
        df['Zip'] = parsed_addresses.apply(lambda x: x['Zip'])
        
        # Save the modified DataFrame back to CSV
        if output_file:
            df.to_csv(output_file, index=False)
            print(f"Address parsing completed successfully. Results saved to '{output_file}'")
        
        return df
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def process_secondsite_csv(input_file='data.csv', output_file='data.csv', address_column='Extracted Address'):
    """
    Process a CSV file to parse addresses from a specified column
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        address_column (str): Name of the column containing addresses
        
    Returns:
        pandas.DataFrame: The processed DataFrame with parsed address columns
    """
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Check if address column exists
        if address_column not in df.columns:
            raise ValueError(f"Error: '{address_column}' column not found in the CSV file.")
        
        # Apply the parser to each address
        parsed_addresses = df[address_column].apply(parse_address)
        
        # Extract the components into new columns
        df['Street2'] = parsed_addresses.apply(lambda x: x['Street'])
        df['City2'] = parsed_addresses.apply(lambda x: x['City'])
        df['State2'] = parsed_addresses.apply(lambda x: x['State'])
        df['Zip2'] = parsed_addresses.apply(lambda x: x['Zip'])
        
        # Save the modified DataFrame back to CSV
        if output_file:
            df.to_csv(output_file, index=False)
            print(f"Address parsing completed successfully. Results saved to '{output_file}'")
        
        return df
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None






def main():
    """
    Main function to run when script is executed directly
    """
    try:
        # Check for usaddress package
        try:
            import usaddress
        except ImportError:
            print("The 'usaddress' package is not installed. Please install it using:")
            print("pip install usaddress")
            print("Falling back to regex parser (less accurate).")
        
        # Process the CSV file
        df = process_csv()
        
        # Print sample of parsed addresses for verification
        if df is not None:
            print("\nSample of parsed addresses:")
            sample_df = df[['Clean Address', 'Street', 'City', 'State', 'Zip']].head(10)
            pd.set_option('display.max_colwidth', None)
            print(sample_df)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()