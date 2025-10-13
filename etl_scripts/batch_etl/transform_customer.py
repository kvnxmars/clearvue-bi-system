#tk's script
"""
=============================================================================
CUSTOMER COLLECTION ETL SCRIPT
ClearVue BI System - MongoDB Data Transformation
=============================================================================

Conceptual Design Target:
{
  "_id": "AKRA01",
  "customer_name": "Akra Trading Ltd",
  "customer_categories": {
    "ccat_code": 27,
    "ccat_desc": "Rustenburg Brits"
  },
  "region": {
    "region_code": "1a",
    "region_desc": "Pretoria Central"
  },
  "rep_code": "010",
  "credit_limit": 3000.0,
  "settle_terms": 0,
  "normal_payterms": 120,
  "discount": 0.0,
  "status": "active"
}
"""

import pandas as pd
import json
from pathlib import Path

# ============================================================================
# 0. SETUP & CONFIGURATION
# ============================================================================

print("\n" + "="*80)
print("CUSTOMER COLLECTION ETL - INITIALIZATION")
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
    # File: Customer.xlsx (contains CUSTOMER_NUMBER, CUSTOMER_NAME, CCAT_CODE, REGION_CODE, CREDIT_LIMIT, etc.)
    customers_df = pd.read_excel(raw_data_dir / "Customer.xlsx", sheet_name="Customer")
    print(f"✓ Loaded Customer.xlsx: {len(customers_df)} records")
    
    # File: Customer_Categories.xlsx (lookup table: CCAT_CODE -> CCAT_DESC)
    customer_categories_df = pd.read_excel(
        raw_data_dir / "Customer Categories.xlsx", 
        sheet_name="Customer_Categories"
    )
    print(f"✓ Loaded Customer Categories.xlsx: {len(customer_categories_df)} records")
    
    # File: Customer_Regions.xlsx (lookup table: REGION_CODE -> REGION_DESC)
    customer_regions_df = pd.read_excel(
        raw_data_dir / "Customer Regions.xlsx",
        sheet_name="Customer_Regions"
    )
    print(f"✓ Loaded Customer Regions.xlsx: {len(customer_regions_df)} records")
    
    
    # File: Customer_Account_Parameters.xlsx (lookup table for customer account types)
    # NOTE: This might be embedded in the main customer record or kept separate
    account_params_df = pd.read_excel(
        raw_data_dir / "Customer Account Parameters.xlsx",
        sheet_name="Customer_Account_Parameters"
    )
    print(f"✓ Loaded Customer Account Parameters.xlsx: {len(account_params_df)} records")
    
    # TODO: Optional - if you have a separate file for representative details
    # File: Representatives.xlsx (lookup: REP_CODE -> REP_DESC, COMMISSION, etc.)
    # representatives_df = pd.read_excel(
    #     raw_data_dir / "Representatives.xlsx",
    #     sheet_name="Representatives"
    # )
    # print(f"✓ Loaded Representatives.xlsx: {len(representatives_df)} records")
    
    print("\n\n")
    
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
# Convert all column names to uppercase and strip whitespace
for df_name, df in [
    ("customers_df", customers_df),
    ("customer_categories_df", customer_categories_df),
    ("customer_regions_df", customer_regions_df),
    ("account_params_df", account_params_df)
]:
    df.columns = df.columns.str.strip().str.upper()
    print(f"✓ Standardized columns in {df_name}")

print()

for df_diagnostic, df in [
    ("Customer Data Columns", customers_df.columns.tolist()),
    ("Customer Categories Columns", customer_categories_df.columns.tolist()),
    ("Customer Regions Columns", customer_regions_df.columns.tolist()),
    ("Account Parameters Columns", account_params_df.columns.tolist())

]:
    print(f"{df_diagnostic}: {df}")
#print(customers_df.columns.tolist())
print()

# TODO: Data type conversions and validations
# CUSTOMER_NUMBER: Should be string (customer IDs are alphanumeric)
customers_df["CUSTOMER_NUMBER"] = customers_df["CUSTOMER_NUMBER"].astype(str).str.strip()
print(f"✓ Standardized CUSTOMER_NUMBER format")


# TODO: Numeric field conversions
# CREDIT_LIMIT, DISCOUNT, SETTLE_TERMS should be numeric
numeric_cols = ["CREDIT_LIMIT", "DISCOUNT", "SETTLE_TERMS", "NORMAL_PAYTERMS"]
for col in numeric_cols:
    if col in customers_df.columns:
        customers_df[col] = pd.to_numeric(customers_df[col], errors="coerce")
        print(f"✓ Converted {col} to numeric")

print()

# TODO: Remove duplicates
initial_count = len(customers_df)
customers_df = customers_df.drop_duplicates(subset=["CUSTOMER_NUMBER"])
print(f"✓ Removed duplicates: {initial_count} -> {len(customers_df)} records\n")


# ============================================================================
# 3. VALIDATE FOREIGN KEYS
# ============================================================================

print("PHASE 3: FOREIGN KEY VALIDATION")
print("-" * 80)

# TODO: Check if all CCAT_CODE values exist in lookup table
valid_ccat_codes = set(customer_categories_df["CCAT_CODE"].unique())
customers_with_invalid_ccat = customers_df[~customers_df["CCAT_CODE"].isin(valid_ccat_codes)]
if len(customers_with_invalid_ccat) > 0:
    print(f"⚠ WARNING: {len(customers_with_invalid_ccat)} customers have invalid CCAT_CODE")
    # TODO: Handle invalid codes (drop, default, or log)
    print("  Action: Removing records with invalid CCAT_CODE")
    customers_df = customers_df[customers_df["CCAT_CODE"].isin(valid_ccat_codes)]
else:
    print(f"✓ All CCAT_CODE values are valid")

# TODO: Check if all REGION_CODE values exist in lookup table
valid_region_codes = set(customer_regions_df["REGION_CODE"].unique())
customers_with_invalid_region = customers_df[~customers_df["REGION_CODE"].isin(valid_region_codes)]
if len(customers_with_invalid_region) > 0:
    print(f"⚠ WARNING: {len(customers_with_invalid_region)} customers have invalid REGION_CODE")
    # TODO: Handle invalid codes
    print("  Action: Removing records with invalid REGION_CODE")
    customers_df = customers_df[customers_df["REGION_CODE"].isin(valid_region_codes)]
else:
    print(f"✓ All REGION_CODE values are valid")

print()


# ============================================================================
# 4. BUILD LOOKUP DICTIONARIES
# ============================================================================

print("PHASE 4: BUILDING LOOKUP DICTIONARIES")
print("-" * 80)

# TODO: Create dictionary mapping CCAT_CODE -> {CCAT_CODE, CCAT_DESC}
# This allows O(1) lookup when building customer documents
ccat_lookup = {}
for _, row in customer_categories_df.iterrows():
    ccat_code = row["CCAT_CODE"]
    ccat_lookup[ccat_code] = {
        "ccat_code": ccat_code,
        "ccat_desc": row.get("CCAT_DESC", "Unknown")
    }
print(f"✓ Built CCAT_CODE lookup: {len(ccat_lookup)} entries")

# TODO: Create dictionary mapping REGION_CODE -> {REGION_CODE, REGION_DESC}
region_lookup = {}
for _, row in customer_regions_df.iterrows():
    region_code = row["REGION_CODE"]
    region_lookup[region_code] = {
        "region_code": region_code,
        "region_desc": row.get("REGION_DESC", "Unknown")
    }
print(f"✓ Built REGION_CODE lookup: {len(region_lookup)} entries")

# TODO: (OPTIONAL) Create dictionary for representatives if REP_CODE exists
# rep_lookup = {}
# if "REP_CODE" in customers_df.columns and representatives_df is not None:
#     for _, row in representatives_df.iterrows():
#         rep_code = row["REP_CODE"]
#         rep_lookup[rep_code] = {
#             "rep_code": rep_code,
#             "rep_desc": row.get("REP_DESC", "Unknown"),
#             "commission": row.get("COMMISSION", 0.0)
#         }
#     print(f"✓ Built REP_CODE lookup: {len(rep_lookup)} entries")

print()


# ============================================================================
# 5. BUILD CUSTOMER COLLECTION DOCUMENTS
# ============================================================================

print("PHASE 5: BUILDING CUSTOMER DOCUMENTS")
print("-" * 80)

customer_collection = []

for _, row in customers_df.iterrows():
    customer_number = row["CUSTOMER_NUMBER"]
    ccat_code = row.get("CCAT_CODE")
    region_code = row.get("REGION_CODE")
    
    # TODO: Build embedded customer_categories object
    customer_categories = ccat_lookup.get(ccat_code, {})
    
    # TODO: Build embedded region object
    region = region_lookup.get(region_code, {})
    
    # TODO: Determine customer status (active/inactive)
    # This might come from a status column or be inferred from other fields
    status = row.get("STATUS", "active").lower()
    # TODO: Add logic if status column doesn't exist:
    # status = "active" if pd.notna(row.get("CUSTOMER_NAME")) else "inactive"
    
    # TODO: Build the complete CUSTOMER document
    doc = {
        "_id": customer_number,
        "customer_categories": customer_categories,
        "region": region,
        "rep_code": row.get("REP_CODE"),  # TODO: Handle null rep codes
        "credit_limit": float(row.get("CREDIT_LIMIT", 0.0)) if pd.notna(row.get("CREDIT_LIMIT")) else 0.0,
        "settle_terms": int(row.get("SETTLE_TERMS", 0)) if pd.notna(row.get("SETTLE_TERMS")) else 0,
        "normal_payterms": int(row.get("NORMAL_PAYTERMS", 0)) if pd.notna(row.get("NORMAL_PAYTERMS")) else 0,
        "discount": float(row.get("DISCOUNT", 0.0)) if pd.notna(row.get("DISCOUNT")) else 0.0,
        "status": status
    }
    
    # TODO: (OPTIONAL) Add account parameters if they exist for this customer
    # customer_acct_params = account_params_df[account_params_df["CUSTOMER_NUMBER"] == customer_number]
    # if len(customer_acct_params) > 0:
    #     doc["account_parameters"] = customer_acct_params["PARAMETER"].tolist()
    # else:
    #     doc["account_parameters"] = []
    
    customer_collection.append(doc)

print(f"✓ Built {len(customer_collection)} CUSTOMER documents\n")


# ============================================================================
# 6. DATA QUALITY CHECKS
# ============================================================================

print("PHASE 6: DATA QUALITY VALIDATION")
print("-" * 80)

# TODO: Check for missing required fields in documents
missing_name = sum(1 for doc in customer_collection if not doc.get("customer_name"))
print(f"Documents with missing customer_name: {missing_name}")

missing_categories = sum(1 for doc in customer_collection if not doc.get("customer_categories"))
print(f"Documents with missing customer_categories: {missing_categories}")

missing_region = sum(1 for doc in customer_collection if not doc.get("region"))
print(f"Documents with missing region: {missing_region}")

# TODO: Check credit limit distribution
credit_limits = [doc.get("credit_limit", 0) for doc in customer_collection]
print(f"Credit limit range: {min(credit_limits):.2f} - {max(credit_limits):.2f}")
print(f"Average credit limit: {sum(credit_limits) / len(credit_limits):.2f}")

print()


# ============================================================================
# 7. EXPORT TO JSON
# ============================================================================

print("PHASE 7: EXPORTING TO JSON")
print("-" * 80)

output_file = raw_data_dir.parent / "customer_collection.json"

try:
    with open(output_file, "w") as f:
        json.dump(customer_collection, f, indent=2)
    
    file_size_kb = output_file.stat().st_size / 1024
    print(f"✓ Successfully exported to: {output_file}")
    print(f"  Total documents: {len(customer_collection)}")
    print(f"  File size: {file_size_kb:.2f} KB\n")
    
except Exception as e:
    print(f"✗ Export failed: {e}\n")
    raise


# ============================================================================
# 8. SAMPLE OUTPUT & VERIFICATION
# ============================================================================

print("PHASE 8: SAMPLE OUTPUT")
print("-" * 80)

if customer_collection:
    print("\nSample CUSTOMER document:")
    print(json.dumps(customer_collection[0], indent=2))
    
    print("\n\nAdditional samples (if available):")
    # TODO: Show a few more examples with different attributes
    for i in [1, 2, 3]:
        if i < len(customer_collection):
            print(f"\nSample {i + 1}:")
            print(json.dumps(customer_collection[i], indent=2))

print("\n" + "="*80)
print("✓ CUSTOMER COLLECTION ETL COMPLETE")
print("="*80 + "\n")