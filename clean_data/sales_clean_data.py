import pandas as pd
import os 

input_folder = (r"C:\Users\nandi\OneDrive\Desktop\SQL Slashers\clearvue-bi-system\raw_data")
output_folder = (r"C:\Users\nandi\OneDrive\Desktop\SQL Slashers\clearvue-bi-system\clean_data")

files = ["Products.xlsx", "Products Styles.xlsx", "Product Brands.xlsx", "Product Categories.xlsx", "Product Ranges.xlsx", "Sales Header.xlsx", "Sales Line.xlsx"]

for file in files :
    file_path = os.path.join(input_folder, file)

    df = pd.read_excel(file_path, engine="openpyxl")
    df = df.drop_duplicates()
    df = df.fillna("Unknown")

    output_name = file.replace (".xlsx", "_clean.json")
    output__path = os.path.join(output_folder, output_name)

    df.to_json(output__path, orient="records", lines=True)

    print (f"Cleand {file} -> saved as {output_name}")

