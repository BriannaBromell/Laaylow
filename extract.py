import subprocess
import sys
import pandas as pd
import os

def install_requirements(requirements_file='requirements.txt'):
    """
    Installs packages from the given requirements.txt file.
    """
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print(f"Successfully installed requirements from '{requirements_file}'")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
    except FileNotFoundError:
        print(f"Error: Requirements file '{requirements_file}' not found.")

def create_requirements_file():
    """
    Creates a basic requirements.txt file if it doesn't exist.
    """
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write('pandas\n')
            f.write('openpyxl\n')
        print("Created a basic 'requirements.txt' file. You can add more dependencies there.")

def extract_descriptions(excel_file, output_folder):
    """
    Extracts text from the first column of an XLSX file and saves each cell's content
    into individual text files in a numbered subfolder.

    Args:
        excel_file (str): Path to the input XLSX file.
        output_folder (str): Name of the subfolder to create for text files.
    """

    try:
        df = pd.read_excel(excel_file)
        print("Column Names:", df.columns)
        if not df.empty:
            first_column_name = df.columns[0]  # Get the name of the first column
            print(f"Using '{first_column_name}' as the description column.")
        else:
            print("Error: The DataFrame is empty. No columns found.")
            return
    except FileNotFoundError:
        print(f"Error: File not found at '{excel_file}'")
        return

    if df.empty:
        return

    os.makedirs(output_folder, exist_ok=True)

    for index, row in df.iterrows():
        first_column_name = df.columns[0]  # Get the name of the first column for each row
        cell_content = str(row[first_column_name])  # Access content using the variable column name
        output_filename = os.path.join(output_folder, f"row_{index + 2}_col_{first_column_name.replace(' ', '_')}.txt") # Use variable in filename
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(cell_content)
    print(f"Extracted {len(df)} descriptions from the first column to '{output_folder}' folder.")

if __name__ == "__main__":
    # Create a basic requirements.txt if it doesn't exist
    create_requirements_file()

    # Install required libraries
    install_requirements()

    excel_file = 'description.xlsx'  # Replace with your file name
    output_folder = 'extracted_descriptions'
    extract_descriptions(excel_file, output_folder)