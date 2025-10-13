# C:\clearvue-bi-system\etl_scripts\batch_etl\transform_supplier.py

import logging
import pandas as pd
from datetime import datetime, timedelta
import os # Import the os module

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the directory of the current script file
# This is the directory: C:\clearvue-bi-system\etl_scripts\batch_etl\
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path to the raw_data directory, which is two levels up from SCRIPT_DIR
# We want to go from ...\batch_etl\ to ...\raw_data\
RAW_DATA_PATH = os.path.join(SCRIPT_DIR, '..', '..', 'raw_data')

# 💡 FIX: Helper function to clean supplier descriptions MUST be defined here
# C:\clearvue-bi-system\etl_scripts\batch_etl\transform_supplier.py (FINAL clean_supplier_desc)

def clean_supplier_desc(desc):
    try:
        if isinstance(desc, str) and desc.startswith("DR"):
            
            # Check for "DR" exactly (with optional surrounding whitespace)
            if desc.strip() == "DR":
                 shipment = ""
            else:
                 # Standard cleaning for "DR " (with space) or "DR something"
                 # 1. Remove "DR " (with space) or just "DR" from the start
                 if desc.startswith("DR "):
                     shipment = desc.replace("DR ", "", 1)
                 else:
                     shipment = desc[2:]
                 
                 # 2. Remove "purch order " and strip whitespace
                 shipment = shipment.replace("purch order ", "", 1).strip()
            
            # Return empty list if 'shipment' is an empty string
            return {"name": "DR Supplier", "shipmentDetails": [shipment] if shipment else []}
            
        return {"name": desc, "shipmentDetails": []}
    except Exception as e:
        logging.error(f"Error cleaning supplier desc {desc}: {e}")
        return {"name": desc, "shipmentDetails": []}

# --------------------------------------------------------------------------------

# Step 1: Extract - Load Excel files from raw_data/
try:
    # Use os.path.join to build the final, correct, absolute file path
    suppliers_path = os.path.join(RAW_DATA_PATH, 'Suppliers.xlsx')
    headers_path = os.path.join(RAW_DATA_PATH, 'Purchases Headers.xlsx')
    lines_path = os.path.join(RAW_DATA_PATH, 'Purchases Lines.xlsx')
    
    suppliers_df = pd.read_excel(suppliers_path)
    headers_df = pd.read_excel(headers_path)
    lines_df = pd.read_excel(lines_path)
    logging.info("Successfully loaded Excel files")
except FileNotFoundError as e:
    logging.error(f"File not found: {e}")
    raise
except Exception as e:
    logging.error(f"Error loading Excel files: {e}")
    raise

# Step 2: Transform - Clean Suppliers
suppliers_df = suppliers_df[suppliers_df['SUPPLIER_CODE'] != "999999"]
suppliers_df['cleaned_supplier'] = suppliers_df['SUPPLIER_DESC'].apply(clean_supplier_desc)
suppliers_df['EXCLSV'] = suppliers_df['EXCLSV'].map({'Y': True, 'N': False})

# Create supplier lookup dictionary
supplier_lookup = {
    row['SUPPLIER_CODE']: {
        'supplierID': row['SUPPLIER_CODE'],
        'name': row['cleaned_supplier']['name'],
        'excludesVAT': row['EXCLSV'],
        'paymentTerms': row['NORMAL_PAYTERMS'],
        'creditLimit': row['CREDIT_LIMIT'],
        'shipmentDetails': row['cleaned_supplier']['shipmentDetails']
    } for _, row in suppliers_df.iterrows()
}

# Step 3: Transform - Clean Purchases Headers

# Convert the column to datetime objects, then format to string YYYY-MM-DD
#  REQUIRED FIX: Add unit and origin for Excel date compatibility
# are processed with 'unit' and 'origin', allowing existing datetimes to be coerced.
headers_df['purchaseDate'] = pd.to_datetime(
    # Convert to numeric; non-numeric (i.e., existing datetimes) will become NaT momentarily
    pd.to_numeric(headers_df['PURCH_DATE'], errors='coerce'), 
    unit='D', 
    origin='1899-12-30',
    errors='coerce'
).dt.strftime('%Y-%m-%d')


# FINANCIAL_PERIOD should be derived from the formatted string
headers_df['financialPeriod'] = headers_df['purchaseDate'].str.replace("-", "").str[:6]

# Validate SUPPLIER_CODE
invalid_suppliers = headers_df[~headers_df['SUPPLIER_CODE'].isin(supplier_lookup.keys())]
if not invalid_suppliers.empty:
    logging.warning(f"Invalid supplier codes found: {invalid_suppliers['SUPPLIER_CODE'].tolist()}")

# Step 4: Transform - Clean Purchases Lines

# 1. Calculate the new total cost, placing it in a temporary column
lines_df['calculatedCost'] = lines_df['QUANTITY'] * lines_df['UNIT_COST_PRICE']

# 2. Check for discrepancies against the original TOTAL_LINE_COST
discrepancies = lines_df[abs(lines_df['calculatedCost'] - lines_df['TOTAL_LINE_COST']) > 0.01]

if not discrepancies.empty:
    logging.warning(f"Cost discrepancies in {discrepancies['PURCH_DOC_NO'].tolist()}")
    # Correct the original column value with the calculated value
    lines_df['TOTAL_LINE_COST'] = lines_df['calculatedCost']

# 3. Drop the temporary calculated cost column
lines_df = lines_df.drop(columns=['calculatedCost'], errors='ignore')

# 4. Rename fields for consistency. 
lines_df = lines_df.rename(columns={
    'INVENTORY_CODE': 'productID',
    'QUANTITY': 'quantity',
    'UNIT_COST_PRICE': 'unitCost',
    'TOTAL_LINE_COST': 'totalCost' # Now holds the corrected value
})

# 5. Explicitly select only the desired columns to remove all old and auxiliary columns
lines_df = lines_df[[
    'PURCH_DOC_NO', 
    'productID', 
    'quantity', 
    'unitCost', 
    'totalCost'
]]


# Step 5: Structure - Combine into MongoDB-compatible documents
purchases_documents = []
for _, header in headers_df.iterrows():
    doc_no = header['PURCH_DOC_NO']
    supplier_id = header['SUPPLIER_CODE']
    
    # Get line items for this PO
    line_items = lines_df[lines_df['PURCH_DOC_NO'] == doc_no][
        ['productID', 'quantity', 'unitCost', 'totalCost']
    ].to_dict('records')
    
    # Compute total purchase cost
    total_cost = sum(item['totalCost'] for item in line_items)
    
    # Build document
    document = {
        '_id': doc_no,
        'purchaseDate': header['purchaseDate'],
        'financialPeriod': header['financialPeriod'],
        'supplier': supplier_lookup.get(supplier_id, {
            'supplierID': supplier_id,
            'name': 'Unknown Supplier',
            'excludesVAT': False,
            'paymentTerms': 0,
            'creditLimit': 0,
            'shipmentDetails': []
        }),
        'lineItems': line_items,
        'totalPurchaseCost': round(total_cost, 2),
        'status': 'Open'
    }
    purchases_documents.append(document)


# Step 6: Load - Save the final documents to a JSON file
import json
from pathlib import Path
# No need for pandas imports here, as we are saving the raw list of dicts.

# Define the output directory (e.g., in a new 'clean_data' folder)
OUTPUT_DIR = Path(SCRIPT_DIR) / '..' / '..' / 'clean_data'
OUTPUT_DIR.mkdir(exist_ok=True) # Create the directory if it doesn't exist

# Define the output file name
OUTPUT_FILE = OUTPUT_DIR / 'purchases_clean.json' 

try:
    with open(OUTPUT_FILE, 'w') as f:
        # json.dump serializes the list of dictionaries
        # indent=4 makes the JSON human-readable and easy to inspect
        json.dump(purchases_documents, f, indent=4)

    logging.info(f"Successfully saved {len(purchases_documents)} MongoDB documents to: {OUTPUT_FILE}")

except Exception as e:
    logging.error(f"Error saving JSON file: {e}")

