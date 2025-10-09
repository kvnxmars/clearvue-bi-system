import logging
import os
import json
from datetime import datetime
from collections import Counter
try:
    import pandas as pd
except ImportError:
    logging.error("pandas module not found. Please install it using 'pip install pandas'")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("=== Starting ETL Process ===")

# ---------------------------------------------------------------------
# 1️⃣ PATH CONFIGURATION
# ---------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
RAW_DIR = os.path.join(BASE_DIR, "raw_data")
CLEAN_DIR = os.path.join(BASE_DIR, "clean_data")

os.makedirs(CLEAN_DIR, exist_ok=True)

logging.info(f"📂 Base Directory: {BASE_DIR}")
logging.info(f"📥 Looking for Excel files in: {RAW_DIR}")
logging.info(f"📤 Clean data will be saved to: {CLEAN_DIR}")

# ---------------------------------------------------------------------
# 2️⃣ HELPER FUNCTION
# ---------------------------------------------------------------------
def excel_to_date(date):
    """Convert Excel serial or datetime to YYYY-MM-DD"""
    try:
        if isinstance(date, (pd.Timestamp, datetime)):
            return date.strftime("%Y-%m-%d")
        numeric_date = pd.to_numeric(date, errors="coerce")
        if pd.isna(numeric_date):
            logging.warning(f"Invalid date format: {date}")
            return None
        return pd.to_datetime(numeric_date, unit="D", origin="1899-12-30").strftime("%Y-%m-%d")
    except Exception as e:
        logging.error(f"Error converting date {date}: {e}")
        return None

# ---------------------------------------------------------------------
# 3️⃣ EXTRACT - LOAD EXCEL FILES
# ---------------------------------------------------------------------
files = [
    "Sales Header.xlsx",
    "Sales Line.xlsx",
    "Products.xlsx",
    "Product Categories.xlsx"
]

dataframes = {}

for file in files:
    path = os.path.join(RAW_DIR, file)
    if not os.path.exists(path):
        logging.error(f"❌ Missing file: {path}")
        dataframes[file] = pd.DataFrame()
    else:
        df = pd.read_excel(path)
        dataframes[file] = df
        logging.info(f"Loaded {file} ({len(df)} rows, {len(df.columns)} cols)")

headers_df = dataframes["Sales Header.xlsx"]
lines_df = dataframes["Sales Line.xlsx"]
products_df = dataframes["Products.xlsx"]
categories_df = dataframes["Product Categories.xlsx"]

# Log raw columns for debugging
logging.info(f"Raw Sales Headers columns: {list(headers_df.columns)}")
logging.info(f"Raw Sales Lines columns: {list(lines_df.columns)}")
logging.info(f"Raw Products columns: {list(products_df.columns)}")
logging.info(f"Raw Product Categories columns: {list(categories_df.columns)}")

# ---------------------------------------------------------------------
# 4️⃣ TRANSFORM - PRODUCTS AND CATEGORIES
# ---------------------------------------------------------------------
if not products_df.empty and not categories_df.empty:
    products_df = products_df[['INVENTORY_CODE', 'PRODCAT_CODE', 'LAST_COST']].dropna(subset=['INVENTORY_CODE'])
    categories_df = categories_df[['PRODCAT_CODE', 'PRODCAT_DESC']].dropna(subset=['PRODCAT_CODE'])
    product_lookup = products_df.merge(categories_df, on='PRODCAT_CODE', how='left').set_index('INVENTORY_CODE')
    product_lookup['PRODCAT_DESC'] = product_lookup['PRODCAT_DESC'].fillna('Unknown')
    product_lookup['LAST_COST'] = pd.to_numeric(product_lookup['LAST_COST'], errors='coerce').fillna(0.0)
    product_lookup = product_lookup[['PRODCAT_DESC', 'LAST_COST']].to_dict('index')
else:
    product_lookup = {}
    logging.warning("Products or Categories data missing — continuing with empty lookup.")

# ---------------------------------------------------------------------
# 5️⃣ TRANSFORM - SALES HEADERS
# ---------------------------------------------------------------------
if not headers_df.empty:
    if 'TRANS_DATE' in headers_df.columns:
        headers_df['saleDate'] = headers_df['TRANS_DATE'].apply(excel_to_date)
    else:
        logging.warning("'TRANS_DATE' column missing in Sales Header file.")
        headers_df['saleDate'] = None

    headers_df = headers_df[headers_df['saleDate'].notnull()]
    headers_df['financialPeriod'] = headers_df['saleDate'].str.replace("-", "", regex=True).str[:6]

    if 'FIN_PERIOD' in headers_df.columns:
        headers_df['FIN_PERIOD'] = headers_df['FIN_PERIOD'].astype(str).str.zfill(6)
        mismatches = headers_df[headers_df['FIN_PERIOD'] != headers_df['financialPeriod']]
        if not mismatches.empty:
            logging.warning(f"Found {len(mismatches)} financial period mismatches: {len(mismatches)} documents affected.")
            logging.info(f"Mismatch sample: {mismatches[['DOC_NUMBER', 'TRANS_DATE', 'FIN_PERIOD', 'financialPeriod']].head().to_dict()}")
            # Create a set of mismatched DOC_NUMBERs for flagging
            mismatched_docs = set(mismatches['DOC_NUMBER'].astype(str))
        else:
            mismatched_docs = set()
    else:
        logging.warning("FIN_PERIOD column missing in Sales Header file.")
        mismatched_docs = set()

    if 'CUSTOMER_NUMBER' in headers_df.columns:
        customer_lookup = {
            code: {'customerID': str(code), 'name': f"Customer {code}"}
            for code in headers_df['CUSTOMER_NUMBER'].dropna().unique()
        }
    else:
        logging.warning("CUSTOMER_NUMBER column not found in Sales Header.")
        customer_lookup = {}
else:
    logging.error("Headers data is empty — skipping transformation.")
    headers_df = pd.DataFrame()
    customer_lookup = {}
    mismatched_docs = set()

# ---------------------------------------------------------------------
# 6️⃣ TRANSFORM - SALES LINES (FINAL ADJUSTMENT FOR RETURNS)
# ---------------------------------------------------------------------
if not lines_df.empty:
    lines_df = lines_df[['DOC_NUMBER', 'INVENTORY_CODE', 'QUANTITY', 'UNIT_SELL_PRICE', 'TOTAL_LINE_PRICE']].copy()
    
    lines_df.loc[:, 'QUANTITY'] = pd.to_numeric(lines_df['QUANTITY'], errors='coerce').fillna(0)
    lines_df.loc[:, 'UNIT_SELL_PRICE'] = pd.to_numeric(lines_df['UNIT_SELL_PRICE'], errors='coerce').fillna(0.0)
    lines_df.loc[:, 'TOTAL_LINE_PRICE'] = pd.to_numeric(lines_df['TOTAL_LINE_PRICE'], errors='coerce').fillna(0.0)
    
    # Log negative value counts
    negative_quantities = lines_df[lines_df['QUANTITY'] < 0]
    logging.info(f"Negative QUANTITY count: {len(negative_quantities)}")
    
    lines_df.loc[:, 'computedTotal'] = lines_df['QUANTITY'] * lines_df['UNIT_SELL_PRICE']
    
    # ✅ FINAL FIX: Use computed magnitude for accuracy, but ensure negative sign for returns.
    lines_df.loc[:, 'totalPrice'] = lines_df.apply(
        lambda row: -abs(row['computedTotal']) if row['QUANTITY'] < 0 else row['computedTotal'], 
        axis=1
    )

    # Check discrepancies for non-return lines only (QTY >= 0)
    discrepancies = lines_df[
        (abs(lines_df['computedTotal'] - lines_df['TOTAL_LINE_PRICE']) > 0.1) & 
        (lines_df['QUANTITY'] >= 0)
    ]
    if not discrepancies.empty:
        logging.warning(f"Price discrepancies found in {len(discrepancies)} non-return lines: {discrepancies['DOC_NUMBER'].tolist()[:3]}...")
        logging.info(f"Sample discrepancies:\n{discrepancies[['DOC_NUMBER', 'QUANTITY', 'UNIT_SELL_PRICE', 'TOTAL_LINE_PRICE', 'computedTotal']].head().to_dict()}")
        
    lines_df.loc[:, 'category'] = lines_df['INVENTORY_CODE'].map(lambda x: product_lookup.get(x, {}).get('PRODCAT_DESC', 'Unknown'))
    lines_df.loc[:, 'lastCost'] = lines_df['INVENTORY_CODE'].map(lambda x: product_lookup.get(x, {}).get('LAST_COST', 0.0))

    lines_df = lines_df.rename(columns={
        'DOC_NUMBER': 'docNumber',
        'QUANTITY': 'quantity',
        'INVENTORY_CODE': 'productID'
    })
    
    lines_df.loc[:, 'docNumber'] = lines_df['docNumber'].astype(str)

    lines_df = lines_df.drop(columns=['UNIT_SELL_PRICE', 'TOTAL_LINE_PRICE', 'computedTotal'], errors='ignore')
else:
    logging.error("Sales Lines data empty — skipping.")
    lines_df = pd.DataFrame()

# ---------------------------------------------------------------------
# 7️⃣ CLEAN DOC_NUMBER IDS (Unchanged)
# ---------------------------------------------------------------------
if not headers_df.empty and 'DOC_NUMBER' in headers_df.columns:
    ids = headers_df['DOC_NUMBER'].dropna().astype(str).str.strip().tolist()
    clean_ids = sorted(set(ids), key=lambda x: int(x[3:]) if x[3:].isdigit() else x)
    logging.info(f"🧾 Found {len(ids)} DOC_NUMBERs ({len(clean_ids)} unique after cleaning).")

    counts = Counter(ids)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    if duplicates:
        logging.warning(f"🔁 Found {len(duplicates)} duplicate DOC_NUMBERs: {duplicates}")
else:
    logging.error("Headers data is empty — skipping ID cleaning.")

# ---------------------------------------------------------------------
# 8️⃣ EXPORT CLEANED DATAFRAMES (Unchanged - Commented Out)
# ---------------------------------------------------------------------
"""
if not headers_df.empty:
    headers_out_path = os.path.join(CLEAN_DIR, "cleaned_headers.csv")
    headers_df.to_csv(headers_out_path, index=False)
    logging.info(f"✅ Cleaned Headers exported → {headers_out_path}")
# ... (rest of CSV exports)
"""

# ---------------------------------------------------------------------
# 9️⃣ STRUCTURE - COMBINE INTO MONGODB-COMPATIBLE DOCUMENTS (Optimized)
# ---------------------------------------------------------------------
sales_documents = []
if not headers_df.empty and not lines_df.empty:
    LINE_ITEM_COLS = ['productID', 'quantity', 'totalPrice', 'category', 'lastCost']

    # 1. OPTIMIZATION: Group Line Items by Document ID
    line_groups = lines_df.groupby('docNumber')[LINE_ITEM_COLS].apply(lambda x: x.to_dict('records'))
    total_price_groups = lines_df.groupby('docNumber')['totalPrice'].sum().round(2)

    if 'DOC_NUMBER' not in headers_df.columns:
        logging.error("Required column 'DOC_NUMBER' missing in headers for join.")
        sales_documents = []
    else:
        # Convert header ID to string for reliable mapping
        headers_df.loc[:, 'DOC_NUMBER_STR'] = headers_df['DOC_NUMBER'].astype(str)
        
        # Reindex and map the grouped data back to the headers
        headers_df.loc[:, 'lineItems'] = headers_df['DOC_NUMBER_STR'].map(line_groups).fillna(pd.Series([[]] * len(headers_df), index=headers_df.index))
        headers_df.loc[:, 'totalSalePrice'] = headers_df['DOC_NUMBER_STR'].map(total_price_groups).fillna(0.0)

        # Filter out headers that didn't match any lines
        docs_with_lines = headers_df[headers_df['lineItems'].apply(len) > 0].copy()
        
        if docs_with_lines.empty:
            logging.warning("No sales documents could be constructed (Headers did not match Lines).")
            sales_documents = []
        else:
            # 2. Final Document Structuring
            for _, header in docs_with_lines.iterrows():
                customer_id = str(header.get('CUSTOMER_NUMBER', 'UNKNOWN'))
                doc_number = header['DOC_NUMBER_STR']
                
                document = {
                    '_id': doc_number,
                    'saleDate': header['saleDate'],
                    'financialPeriod': header['financialPeriod'],
                    'customer': customer_lookup.get(customer_id, {
                        'customerID': customer_id,
                        'name': 'Unknown Customer'
                    }),
                    'lineItems': header['lineItems'],
                    'totalSalePrice': float(header['totalSalePrice']),
                    'status': 'Completed',
                    'financialPeriodMismatch': doc_number in mismatched_docs
                }
                sales_documents.append(document)
            
            logging.info(f"✅ Created {len(sales_documents)} MongoDB-compatible sales documents.")

else:
    logging.error("Headers or Lines data empty — skipping document creation.")
    sales_documents = []

# ---------------------------------------------------------------------
# 🔟 OUTPUT - SAVE TO JSON FOR MONGODB (Unchanged)
# ---------------------------------------------------------------------
if sales_documents:
    output_path = os.path.join(CLEAN_DIR, "sales.json")
    try:
        with open(output_path, "w") as f:
            json.dump(sales_documents, f, indent=2)
        logging.info(f"✅ Saved {len(sales_documents)} documents to {output_path}")
    except Exception as e:
        logging.error(f"Error saving JSON output: {e}")
        raise
else:
    logging.warning("No sales documents generated — skipping JSON output.")

# Log sample document
logging.info(f"Generated {len(sales_documents)} documents")
if sales_documents:
    logging.info("Sample document:")
    logging.info(json.dumps(sales_documents[0], indent=2))

# ---------------------------------------------------------------------
# 1️⃣1️⃣ SUMMARY (Updated)
# ---------------------------------------------------------------------
logging.info("=== ETL Summary ===")
logging.info(f"Headers: {len(headers_df)} rows")
logging.info(f"Lines: {len(lines_df)} rows")
logging.info(f"Products: {len(products_df)} rows")
logging.info(f"Categories: {len(categories_df)} rows")
logging.info(f"Sales Documents: {len(sales_documents)} documents")
logging.info(f"Negative QUANTITY count: {len(lines_df[lines_df['quantity'] < 0])}")
logging.info(f"Negative totalPrice count: {len(lines_df[lines_df['totalPrice'] < 0])}")
logging.info("=== ETL Completed Successfully ===")