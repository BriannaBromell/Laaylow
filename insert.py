import subprocess
import sys
import pandas as pd
import os
import shutil

""" Author: https://www.reddit.com/user/BriannaBromell/ """

def install_requirements(requirements_file='requirements.txt'):
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
        print(f"Installed requirements from '{requirements_file}'")
    except subprocess.CalledProcessError as e:
        print(f"Install error: {e}")
    except FileNotFoundError:
        print(f"Missing: {requirements_file}")

def create_requirements_file():
    if not os.path.exists('requirements.txt'):
        with open('requirements.txt', 'w') as f:
            f.write('pandas\nopenpyxl\n')
        print("Created requirements.txt")

def insert_descriptions(original_excel_file, input_folder):
    if not os.path.exists(input_folder):
        print(f"Missing folder: {input_folder}")
        return

    try:
        df_original = pd.read_excel(original_excel_file)
        first_col = df_original.columns[0]
        new_file = original_excel_file.replace('.xlsx', '_new.xlsx')
        shutil.copyfile(original_excel_file, new_file)
        print(f"Copied to {new_file}")
    except Exception as e:
        print(f"File error: {e}")
        return

    updates = {}
    for filename in os.listdir(input_folder):
        if filename.startswith("row_") and filename.endswith(".txt"):
            try:
                # Extract row number from filename pattern: row_X_*
                base_name = os.path.splitext(filename)[0]
                parts = base_name.split("_")
                row_num = int(parts[1])  # parts[1] = X in row_X
                
                with open(os.path.join(input_folder, filename), 'r', encoding='utf-8') as f:
                    updates[row_num] = f.read()
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    try:
        df_new = pd.read_excel(new_file)
        updated = 0
        for idx in df_new.index:
            excel_row = idx + 2  # Data starts at row 2
            if excel_row in updates:
                df_new.at[idx, first_col] = updates[excel_row]
                updated += 1
        
        df_new.to_excel(new_file, index=False)
        print(f"Updated {updated} rows in {new_file}")

    except Exception as e:
        print(f"Excel error: {e}")

if __name__ == "__main__":
    create_requirements_file()
    install_requirements()
    insert_descriptions('description.xlsx', 'reworded_descriptions')  # Change folder as needed