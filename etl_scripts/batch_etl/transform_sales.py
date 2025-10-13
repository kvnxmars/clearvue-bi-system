#nandi & ishmael's script

"""
=============================================================================
SALES COLLECTION ETL SCRIPT
ClearVue BI System - MongoDB Data Transformation
=============================================================================

Conceptual Design Target:
{
  "_id": "DC700467",
  "trans_type_code": "2",
  "trans_type_desc": "CREDIT NOTE",
  "customer_number": "ESP100",
  "rep_code": "02JUL",
  "trans_date": "2019-03-25",
  "fin_period": "201901",
  "total_revenue": 1000.0,
  "total_cost": 500.0,
  "line_items": [
    {
      "inventory_code": "123ABC",
      "quantity": 2,
      "unit_sell_price": 500.0,
      "unit_cost": 250.0,
      "total_line_price": 1000.0,
      "profit": 500.0
    }
  ]
}
"""

import pandas as pd
import json
from pathlib import Path

# ============================================================================
# 0. SETUP & CONFIGURATION
# ============================================================================

print("\n" + "="*80)
print("SALES COLLECTION ETL - INITIALIZATION")
print("="*80 + "\n")

# Get script directory and raw_data path
script_dir = Path(__file__).parent
raw_data_dir = script_dir.parent.parent / "raw_data"

print(f"Script location: {script_dir}")
print(f"Raw data location: {raw_data_dir}\n")

# ============================================================================
# 1. LOAD SOURCE FILES
# ============================================================================

print("PHASE 1: LOADING SOURCE FILES")
print("-" * 80)

try:
    # TODO: Replace with actual file names when ready
    # File: Sales_Header.xlsx (contains DOC_NUMBER, CUSTOMER_NUMBER, REP_CODE, TRANS_DATE, TRANS_TYPE_CODE, etc.)
    sales_header_df = pd.read_excel(raw_data_dir / "Sales Header.xlsx", sheet_name="Sales_Header")
    print(f"✓ Loaded Sales Header.xlsx: {len(sales_header_df)} records")
    
    # TODO: Replace with actual file name
    # File: Sales_Lines.xlsx (contains DOC_NUMBER, INVENTORY_CODE, QUANTITY, UNIT_SELL_PRICE, UNIT_COST, TOTAL_LINE_PRICE)
    sales_lines_df = pd.read_excel(raw_data_dir / "Sales Line.xlsx", sheet_name="Sales_Line")
    print(f"✓ Loaded Sales Lines.xlsx: {len(sales_lines_df)} records")
    
    # TODO: Replace with actual file name
    # File: Trans_Types.xlsx (lookup table: TRANS_TYPE_CODE -> TRANS_TYPE_DESC)
    trans_types_df = pd.read_excel(raw_data_dir / "Trans Types.xlsx", sheet_name="Trans_Types")
    print(f"✓ Loaded Trans Types.xlsx: {len(trans_types_df)} records")
    
    # TODO: Optional - Product dimensional data for enrichment
    # File: Products.xlsx (contains INVENTORY_CODE, PRODUCT_NAME, PRODCAT_CODE, etc.)
    # products_df = pd.read_excel(raw_data_dir / "Products.xlsx", sheet_name="Products")
    # print(f"✓ Loaded Products.xlsx: {len(products_df)} records")
    
    # TODO: Optional - Product Styles for enrichment
    # File: Product_Styles.xlsx (contains INVENTORY_CODE, GENDER, MATERIAL, STYLE, etc.)
    # product_styles_df = pd.read_excel(raw_data_dir / "Product Styles.xlsx", sheet_name="Product_Styles")
    # print(f"✓ Loaded Product Styles.xlsx: {len(product_styles_df)} records")
    
    print("\n")
    
except FileNotFoundError as e:
    print(f"✗ FILE NOT FOUND: {e}")
    print("Make sure all required Excel files are in the raw_data directory")
    raise


# ============================================================================
# 2. STANDARDIZE & CLEAN DATA
# ============================================================================

print("PHASE 2: DATA STANDARDIZATION & CLEANING")
print("-" * 80)

# TODO: Standardize column names across all dataframes
for df_name, df in [
    ("sales_header_df", sales_header_df),
    ("sales_lines_df", sales_lines_df),
    ("trans_types_df", trans_types_df)
]:
    df.columns = df.columns.str.strip().str.upper()
    print(f"✓ Standardized columns in {df_name}")

print()

# TODO: Sales Header data cleaning
# DOC_NUMBER: Primary key - should be string
sales_header_df["DOC_NUMBER"] = sales_header_df["DOC_NUMBER"].astype(str).str.strip()
print(f"✓ Standardized DOC_NUMBER format")

# CUSTOMER_NUMBER: Should be string
sales_header_df["CUSTOMER_NUMBER"] = sales_header_df["CUSTOMER_NUMBER"].astype(str).str.strip()
print(f"✓ Standardized CUSTOMER_NUMBER format")

# TRANS_DATE: Convert to datetime
sales_header_df["TRANS_DATE"] = pd.to_datetime(sales_header_df["TRANS_DATE"], errors="coerce")
print(f"✓ Converted TRANS_DATE to datetime")

# TODO: Generate FIN_PERIOD from TRANS_DATE if not already present
if "FIN_PERIOD" not in sales_header_df.columns and "TRANS_DATE" in sales_header_df.columns:
    sales_header_df["FIN_PERIOD"] = sales_header_df["TRANS_DATE"].dt.strftime("%Y%m").astype(int)
    print(f"✓ Generated FIN_PERIOD from TRANS_DATE")

# TODO: Handle missing REP_CODE (fill with default or keep null)
if "REP_CODE" in sales_header_df.columns:
    sales_header_df["REP_CODE"] = sales_header_df["REP_CODE"].astype(str).str.strip()
    print(f"✓ Standardized REP_CODE format")

# Remove duplicates from header
initial_count = len(sales_header_df)
sales_header_df = sales_header_df.drop_duplicates(subset=["DOC_NUMBER"])
print(f"✓ Removed duplicate headers: {initial_count} -> {len(sales_header_df)} records\n")

# TODO: Sales Lines data cleaning
# DOC_NUMBER: Link to header
sales_lines_df["DOC_NUMBER"] = sales_lines_df["DOC_NUMBER"].astype(str).str.strip()
print(f"✓ Standardized Sales Lines DOC_NUMBER")

# INVENTORY_CODE: Product identifier
sales_lines_df["INVENTORY_CODE"] = sales_lines_df["INVENTORY_CODE"].astype(str).str.strip()
print(f"✓ Standardized INVENTORY_CODE format")

# Numeric conversions: QUANTITY, UNIT_SELL_PRICE, UNIT_COST, TOTAL_LINE_PRICE
numeric_cols_lines = ["QUANTITY", "UNIT_SELL_PRICE", "UNIT_COST", "TOTAL_LINE_PRICE"]
for col in numeric_cols_lines:
    if col in sales_lines_df.columns:
        sales_lines_df[col] = pd.to_numeric(sales_lines_df[col], errors="coerce")
        print(f"✓ Converted {col} to numeric")

# Remove duplicates from lines
initial_count = len(sales_lines_df)
sales_lines_df = sales_lines_df.drop_duplicates()
print(f"✓ Removed duplicate lines: {initial_count} -> {len(sales_lines_df)} records\n")


# ============================================================================
# 3. VALIDATE FOREIGN KEYS
# ============================================================================

print("PHASE 3: FOREIGN KEY VALIDATION")
print("-" * 80)

# TODO: Check if all DOC_NUMBER in sales_lines exist in sales_header
valid_doc_numbers = set(sales_header_df["DOC_NUMBER"].unique())
lines_with_invalid_doc = sales_lines_df[~sales_lines_df["DOC_NUMBER"].isin(valid_doc_numbers)]
if len(lines_with_invalid_doc) > 0:
    print(f"⚠ WARNING: {len(lines_with_invalid_doc)} sales lines have invalid DOC_NUMBER")
    print("  Action: Removing orphaned sales lines")
    sales_lines_df = sales_lines_df[sales_lines_df["DOC_NUMBER"].isin(valid_doc_numbers)]
else:
    print(f"✓ All sales lines link to valid sales headers")

# TODO: Check if all TRANS_TYPE_CODE values exist in lookup table
if "TRANS_TYPE_CODE" in sales_header_df.columns and "TRANS_TYPE_CODE" in trans_types_df.columns:
    valid_trans_types = set(trans_types_df["TRANS_TYPE_CODE"].unique())
    headers_with_invalid_type = sales_header_df[~sales_header_df["TRANS_TYPE_CODE"].isin(valid_trans_types)]
    if len(headers_with_invalid_type) > 0:
        print(f"⚠ WARNING: {len(headers_with_invalid_type)} sales headers have invalid TRANS_TYPE_CODE")
        print("  Action: Removing records with invalid TRANS_TYPE_CODE")
        sales_header_df = sales_header_df[sales_header_df["TRANS_TYPE_CODE"].isin(valid_trans_types)]
    else:
        print(f"✓ All TRANS_TYPE_CODE values are valid")

print()


# ============================================================================
# 4. BUILD LOOKUP DICTIONARIES
# ============================================================================

print("PHASE 4: BUILDING LOOKUP DICTIONARIES")
print("-" * 80)

# TODO: Create dictionary mapping TRANS_TYPE_CODE -> {TRANS_TYPE_CODE, TRANS_TYPE_DESC}
trans_types_lookup = {}
if "TRANS_TYPE_CODE" in trans_types_df.columns:
    for _, row in trans_types_df.iterrows():
        trans_code = row["TRANS_TYPE_CODE"]
        trans_types_lookup[trans_code] = {
            "trans_type_code": trans_code,
            "trans_type_desc": row.get("TRANS_TYPE_DESC", "Unknown")
        }
    print(f"✓ Built TRANS_TYPE_CODE lookup: {len(trans_types_lookup)} entries")

print()


# ============================================================================
# 5. AGGREGATE SALES LINES BY DOCUMENT
# ============================================================================

print("PHASE 5: AGGREGATING SALES LINES BY DOCUMENT")
print("-" * 80)

# TODO: Group sales lines by DOC_NUMBER and create nested array of line items
# This creates the line_items array that will be embedded in each sales document
sales_lines_grouped = {}

for doc_number in sales_lines_df["DOC_NUMBER"].unique():
    doc_lines = sales_lines_df[sales_lines_df["DOC_NUMBER"] == doc_number]
    
    line_items = []
    for _, line in doc_lines.iterrows():
        # TODO: Calculate profit for each line (TOTAL_LINE_PRICE - (QUANTITY * UNIT_COST))
        quantity = line.get("QUANTITY", 0)
        unit_cost = line.get("UNIT_COST", 0)
        total_line_price = line.get("TOTAL_LINE_PRICE", 0)
        
        # Profit calculation: revenue - cost
        profit = total_line_price - (quantity * unit_cost)
        
        line_item = {
            "inventory_code": line.get("INVENTORY_CODE"),
            "quantity": int(quantity) if pd.notna(quantity) else 0,
            "unit_sell_price": float(line.get("UNIT_SELL_PRICE", 0.0)) if pd.notna(line.get("UNIT_SELL_PRICE")) else 0.0,
            "unit_cost": float(unit_cost) if pd.notna(unit_cost) else 0.0,
            "total_line_price": float(total_line_price) if pd.notna(total_line_price) else 0.0,
            "profit": float(profit)
        }
        
        # TODO: (OPTIONAL) Embed product dimensions if available
        # This would add fields like GENDER, MATERIAL, STYLE, PRODUCT_CATEGORY, etc.
        # if products_df is not None and product_styles_df is not None:
        #     product_info = products_df[products_df["INVENTORY_CODE"] == line.get("INVENTORY_CODE")]
        #     if len(product_info) > 0:
        #         line_item["product_name"] = product_info.iloc[0].get("PRODUCT_NAME")
        #         line_item["product_category"] = product_info.iloc[0].get("PRODCAT_CODE")
        
        line_items.append(line_item)
    
    sales_lines_grouped[doc_number] = line_items

print(f"✓ Aggregated {len(sales_lines_grouped)} sales documents\n")


# ============================================================================
# 6. BUILD SALES COLLECTION DOCUMENTS
# ============================================================================

print("PHASE 6: BUILDING SALES DOCUMENTS")
print("-" * 80)

sales_collection = []

for _, header_row in sales_header_df.iterrows():
    doc_number = header_row["DOC_NUMBER"]
    trans_type_code = header_row.get("TRANS_TYPE_CODE")
    
    # TODO: Lookup transaction type description
    trans_type_obj = trans_types_lookup.get(trans_type_code, {})
    
    # TODO: Get aggregated line items for this document
    line_items = sales_lines_grouped.get(doc_number, [])
    
    # TODO: Calculate totals from line items
    total_revenue = sum(item.get("total_line_price", 0) for item in line_items)
    total_cost = sum(item.get("quantity", 0) * item.get("unit_cost", 0) for item in line_items)
    total_profit = sum(item.get("profit", 0) for item in line_items)
    
    # TODO: Build the complete SALES document
    doc = {
        "_id": doc_number,
        "trans_type_code": trans_type_code,
        "trans_type_desc": trans_type_obj.get("trans_type_desc", "Unknown"),
        "customer_number": header_row.get("CUSTOMER_NUMBER"),
        "rep_code": header_row.get("REP_CODE"),
        "trans_date": header_row.get("TRANS_DATE").isoformat() if pd.notna(header_row.get("TRANS_DATE")) else None,
        "fin_period": str(int(header_row.get("FIN_PERIOD"))) if pd.notna(header_row.get("FIN_PERIOD")) else None,
        "total_revenue": float(total_revenue),
        "total_cost": float(total_cost),
        "total_profit": float(total_profit),
        "line_items": line_items
    }
    
    sales_collection.append(doc)

print(f"✓ Built {len(sales_collection)} SALES documents\n")


# ============================================================================
# 7. DATA QUALITY CHECKS
# ============================================================================

print("PHASE 7: DATA QUALITY VALIDATION")
print("-" * 80)

# TODO: Check for documents with no line items
docs_no_lines = sum(1 for doc in sales_collection if not doc.get("line_items", []))
print(f"Documents with no line items: {docs_no_lines}")

# TODO: Check for missing key fields
missing_customer = sum(1 for doc in sales_collection if not doc.get("customer_number"))
print(f"Documents with missing customer_number: {missing_customer}")

missing_trans_date = sum(1 for doc in sales_collection if not doc.get("trans_date"))
print(f"Documents with missing trans_date: {missing_trans_date}")

# TODO: Revenue and cost distribution checks
revenues = [doc.get("total_revenue", 0) for doc in sales_collection]
costs = [doc.get("total_cost", 0) for doc in sales_collection]
profits = [doc.get("total_profit", 0) for doc in sales_collection]

print(f"\nRevenue range: {min(revenues):.2f} - {max(revenues):.2f}")
print(f"Average revenue: {sum(revenues) / len(revenues):.2f}")
print(f"Total revenue: {sum(revenues):.2f}")

print(f"\nTotal cost: {sum(costs):.2f}")
print(f"Total profit: {sum(profits):.2f}")

print()


# ============================================================================
# 8. EXPORT TO JSON
# ============================================================================

print("PHASE 8: EXPORTING TO JSON")
print("-" * 80)

output_file = raw_data_dir.parent / "sales_collection.json"

try:
    with open(output_file, "w") as f:
        json.dump(sales_collection, f, indent=2)
    
    file_size_kb = output_file.stat().st_size / 1024
    print(f"✓ Successfully exported to: {output_file}")
    print(f"  Total documents: {len(sales_collection)}")
    print(f"  File size: {file_size_kb:.2f} KB\n")
    
except Exception as e:
    print(f"✗ Export failed: {e}\n")
    raise


# ============================================================================
# 9. SAMPLE OUTPUT & VERIFICATION
# ============================================================================

print("PHASE 9: SAMPLE OUTPUT")
print("-" * 80)

if sales_collection:
    print("\nSample SALES document:")
    print(json.dumps(sales_collection[0], indent=2))
    
    print("\n\nAdditional samples (if available):")
    # TODO: Show a few more examples
    for i in [1, 2, 3]:
        if i < len(sales_collection):
            print(f"\nSample {i + 1}:")
            print(json.dumps(sales_collection[i], indent=2))

print("\n" + "="*80)
print("✓ SALES COLLECTION ETL COMPLETE")
print("="*80 + "\n")