import subprocess
import sys
import pandas as pd
import os
import shutil

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

def insert_descriptions(original_excel_file, input_folder):
    """
    Copies the original Excel file, reads the modified text files,
    and inserts their content back into the first column of the new Excel file.

    Args:
        original_excel_file (str): Path to the original XLSX file.
        input_folder (str): Path to the folder containing the modified text files.
    """
    try:
        df_original = pd.read_excel(original_excel_file)
        first_column_name = df_original.columns[0]
        new_excel_file = original_excel_file.replace('.xlsx', '_new.xlsx')
        shutil.copyfile(original_excel_file, new_excel_file)
        print(f"Copied '{original_excel_file}' to '{new_excel_file}'")
        print(f"Please wait...")
    except FileNotFoundError:
        print(f"Error: Original Excel file not found at '{original_excel_file}'")
        return
    except Exception as e:
        print(f"Error copying Excel file: {e}")
        return

    updated_descriptions = {}
    for filename in os.listdir(input_folder):
        if filename.startswith("row_") and filename.endswith(".txt"):
            try:
                parts = filename.split("_")
                row_num = int(parts[1])
                filepath = os.path.join(input_folder, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    updated_descriptions[row_num] = f.read()
            except ValueError:
                print(f"Warning: Could not parse row number from filename: {filename}")
            except Exception as e:
                print(f"Error reading file '{filename}': {e}")

    try:
        df_new = pd.read_excel(new_excel_file)
        updated_count = 0
        for index, row in df_new.iterrows():
            excel_row_num = index + 2  # Assuming data starts from row 2
            if excel_row_num in updated_descriptions:
                df_new.loc[index, first_column_name] = updated_descriptions[excel_row_num]
                updated_count += 1

        df_new.to_excel(new_excel_file, index=False)
        print(f"Successfully inserted {updated_count} updated descriptions into '{new_excel_file}'.")

    except FileNotFoundError:
        print(f"Error: New Excel file not found at '{new_excel_file}' (this should not happen).")
    except KeyError:
        print(f"Error: First column '{first_column_name}' not found in the new Excel file.")
    except Exception as e:
        print(f"Error writing to the new Excel file: {e}")

if __name__ == "__main__":
    # Create a basic requirements.txt if it doesn't exist
    create_requirements_file()

    # Install required libraries
    install_requirements()

    original_excel_file = 'description.xlsx'  # Replace with your original file name
    input_folder = 'extracted_descriptions'  # Replace with the folder containing the modified text files
    insert_descriptions(original_excel_file, input_folder)