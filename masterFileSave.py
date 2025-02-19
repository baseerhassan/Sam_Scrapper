import csv
import os
class TableData:
    def __init__(self, headers=None):
        """
        Initialize the TableData object.
        
        :param headers: List of column headers (optional).
        """
        self.headers = headers if headers else []
        self.data = []  # List to hold table rows (each row is a list of values)

    def write_to_csv(table_data, csv_filename):
       
        current_directory = os.getcwd()
        csv_file_path = os.path.join(current_directory, csv_filename)

        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write each row of table_data to the CSV file
            for row in table_data:
                writer.writerow(row)

        print(f"Data has been written to {csv_file_path}")
