import pandas as pd
import os

# Load Excel
file_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Sales Header.xlsx"
df = pd.read_excel(file_path)

print("Original data shape:", df.shape)
print("\nFirst few rows:")
print(df.head())

# 1. Check for missing values
print("\nMissing values before cleaning:")
print(df.isnull().sum())

# 2. Check data types
print("\nData types:")
print(df.dtypes)

# 3. Clean TRANS_DATE - remove time component if it's all zeros
# Changed: Extract just the date part since time is always 00:00:00
if 'TRANS_DATE' in df.columns:
    df['TRANS_DATE'] = pd.to_datetime(df['TRANS_DATE']).dt.date
    print("\nTRANS_DATE cleaned - time component removed")

# 4. Clean REP_CODE - categorize and standardize
# Changed: Create categories for better analysis and grouping
if 'REP_CODE' in df.columns:
    # Identify special codes vs regular rep codes
    special_codes = ['CONS', 'STOCK', 'SAMPL', 'STAND', 'XX', 'REP']
    df['REP_CATEGORY'] = 'REGULAR'
    
    for code in special_codes:
        mask = df['REP_CODE'].astype(str).str.contains(code, na=False)
        df.loc[mask, 'REP_CATEGORY'] = code
    
    # For regular codes, extract the base code (first 2 characters)
    regular_mask = df['REP_CATEGORY'] == 'REGULAR'
    df.loc[regular_mask, 'REP_BASE_CODE'] = df.loc[regular_mask, 'REP_CODE'].astype(str).str[:2]
    
    print("\nREP_CODE categorized:")
    print(df['REP_CATEGORY'].value_counts())

# 5. Clean CUSTOMER_NUMBER - validate patterns
# Changed: Flag potential invalid customer numbers
if 'CUSTOMER_NUMBER' in df.columns:
    # Flag suspicious patterns
    df['CUSTOMER_VALID'] = True
    df.loc[df['CUSTOMER_NUMBER'].astype(str) == '999999', 'CUSTOMER_VALID'] = False
    
    print(f"\nCustomer numbers with '999999': {len(df[df['CUSTOMER_NUMBER'].astype(str) == '999999'])}")

# 6. Validate FIN_PERIOD against TRANS_DATE
# Changed: Check if FIN_PERIOD matches the year/month from TRANS_DATE
if 'TRANS_DATE' in df.columns and 'FIN_PERIOD' in df.columns:
    df['CALCULATED_PERIOD'] = pd.to_datetime(df['TRANS_DATE']).dt.strftime('%Y%m')
    df['PERIOD_MATCH'] = df['FIN_PERIOD'].astype(str) == df['CALCULATED_PERIOD']
    
    mismatch_count = len(df[~df['PERIOD_MATCH']])
    print(f"\nFIN_PERIOD mismatches: {mismatch_count}")
    
    if mismatch_count > 0:
        print("Sample mismatches:")
        print(df[~df['PERIOD_MATCH']][['TRANS_DATE', 'FIN_PERIOD', 'CALCULATED_PERIOD']].head())

# 7. Check DOC_NUMBER sequence and duplicates
# Changed: Validate document number sequence and check for duplicates
if 'DOC_NUMBER' in df.columns:
    duplicates = df.duplicated(subset=['DOC_NUMBER']).sum()
    print(f"\nDuplicate DOC_NUMBER entries: {duplicates}")
    
    # Convert to numeric where possible to check sequence
    df['DOC_NUMBER_NUMERIC'] = pd.to_numeric(df['DOC_NUMBER'].str.replace(r'[^\d]', '', regex=True), errors='coerce')

# 8. Clean TRANSTYPE_CODE - ensure it's numeric
# Changed: Convert to numeric and handle any non-numeric values
if 'TRANSTYPE_CODE' in df.columns:
    df['TRANSTYPE_CODE'] = pd.to_numeric(df['TRANSTYPE_CODE'], errors='coerce')
    print(f"\nTRANSTYPE_CODE unique values: {df['TRANSTYPE_CODE'].unique()}")

# 9. Remove unnecessary columns created during cleaning
columns_to_drop = ['CALCULATED_PERIOD', 'PERIOD_MATCH', 'DOC_NUMBER_NUMERIC']
df_cleaned = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

# 10. Final data quality check
print("\n" + "="*50)
print("CLEANING SUMMARY")
print("="*50)
print(f"Final data shape: {df_cleaned.shape}")
print(f"Missing values after cleaning:")
print(df_cleaned.isnull().sum())

print(f"\nREP_CODE categories created:")
print(df_cleaned['REP_CATEGORY'].value_counts())

# Save cleaned data
output_dir = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "Sales_Header_Cleaned.xlsx")
df_cleaned.to_excel(output_path, index=False)

print(f"\nCleaned data saved to: {output_path}")

# Save a summary report
summary_report = f"""
SALES HEADER DATA CLEANING REPORT
==================================

Original Records: {df.shape[0]}
Final Records: {df_cleaned.shape[0]}

CLEANING OPERATIONS PERFORMED:
1. TRANS_DATE: Removed time component (was always 00:00:00)
2. REP_CODE: Categorized into REGULAR/CONS/STOCK/SAMPL/STAND/XX/REP
3. CUSTOMER_NUMBER: Flagged invalid entries (999999)
4. FIN_PERIOD: Validated against TRANS_DATE
5. DOC_NUMBER: Checked for duplicates
6. TRANSTYPE_CODE: Ensured numeric format

DATA QUALITY METRICS:
- REP_CODE Categories: {dict(df_cleaned['REP_CATEGORY'].value_counts())}
- Invalid Customer Numbers: {len(df_cleaned[~df_cleaned['CUSTOMER_VALID']])}
- Missing Values: {df_cleaned.isnull().sum().to_dict()}
"""

print(summary_report)

# Save summary to text file
summary_path = os.path.join(output_dir, "Sales_Header_Cleaning_Report.txt")
with open(summary_path, 'w') as f:
    f.write(summary_report)

print(f"Cleaning report saved to: {summary_path}")

import pandas as pd
import os

# Load Sales Header data
file_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Sales Header.xlsx"
df = pd.read_excel(file_path)

print("Original data shape:", df.shape)

# 1. Clean TRANS_DATE - remove time component
if 'TRANS_DATE' in df.columns:
    df['TRANS_DATE'] = pd.to_datetime(df['TRANS_DATE']).dt.date
    print("TRANS_DATE cleaned - time component removed")

# 2. Enhanced REP_CODE categorization based on ACTUAL business definitions
def categorize_rep_code(rep_code):
    """Categorize REP_CODE based on actual business definitions from Reps file"""
    code_str = str(rep_code)
    
    # Sales Representatives (actual people)
    if code_str in ['02', '03', '04', '05', '06', '07', '01', '010']:
        return 'SALES_REP'
    elif any(code_str.startswith(prefix) for prefix in ['02', '03', '04', '05', '06', '07', '01']):
        if 'C' in code_str and len(code_str) == 3:  # Like '02C', '03C'
            return 'CONSIGNMENT_ACCOUNT'
        elif any(suffix in code_str for suffix in ['JUL', 'CHE', 'MYR', 'EDN']):
            return 'CROSS_TERRITORY_SALE'
        elif any(suffix in code_str for suffix in ['RO*', 'MA*', 'RA*', 'BJ*']):
            return 'DISCOUNT_CUSTOMER'
        else:
            return 'SALES_REP_SPECIAL'
    
    # Consignments
    elif 'CONS' in code_str:
        return 'CONSIGNMENT'
    
    # Special business processes
    elif code_str == 'STOCK':
        return 'STOCK_MOVEMENT'
    elif code_str == 'SAMPL':
        return 'SAMPLES'
    elif 'STAND' in code_str:
        return 'STANDS_DISPLAY'
    elif code_str == 'XX':
        return 'HOUSE_CONSIGNMENT'
    elif code_str == 'REP':
        return 'REPAIRS'
    elif code_str == 'DISC':
        return 'DISCOUNT_SPECIALS'
    elif code_str == 'PROMO':
        return 'PROMOTION'
    
    # Problem accounts
    elif code_str.startswith('ZZZ'):
        return 'PROBLEM_ACCOUNT'
    
    else:
        return 'OTHER'

# Apply the categorization
df['REP_CATEGORY'] = df['REP_CODE'].apply(categorize_rep_code)

# 3. Extract Sales Rep ID for actual sales reps
def extract_rep_id(rep_code):
    """Extract the main sales rep ID (02, 03, 04, etc.)"""
    code_str = str(rep_code)
    if code_str[:2].isdigit():
        return code_str[:2]
    return None

df['SALES_REP_ID'] = df['REP_CODE'].apply(extract_rep_id)

# 4. Clean CUSTOMER_NUMBER
if 'CUSTOMER_NUMBER' in df.columns:
    df['CUSTOMER_VALID'] = ~df['CUSTOMER_NUMBER'].isin(['999999'])

# 5. Clean other columns (same as before)
if 'TRANSTYPE_CODE' in df.columns:
    df['TRANSTYPE_CODE'] = pd.to_numeric(df['TRANSTYPE_CODE'], errors='coerce')

# 6. Show results
print("\nREP_CODE Categories (based on ACTUAL business definitions):")
print(df['REP_CATEGORY'].value_counts())

print(f"\nSales Rep Distribution:")
print(df['SALES_REP_ID'].value_counts())

# Save cleaned data
output_dir = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data"
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "Sales_Header_Cleaned.xlsx")
df.to_excel(output_path, index=False)

print(f"\nCleaned data saved to: {output_path}")

# Create a mapping summary
category_mapping = {
    'SALES_REP': 'Actual sales representatives (02=R, 03=BJ, 04=BM, etc.)',
    'CONSIGNMENT': 'Consignment sales (CONS, CONS2, CONS3, etc.)',
    'CONSIGNMENT_ACCOUNT': 'Consignment sales accounts (02C, 03C, etc.)',
    'CROSS_TERRITORY_SALE': 'Sales in other territories (02JUL, 03CHE, etc.)',
    'DISCOUNT_CUSTOMER': 'Discount customers (02RO*, 04MA*, etc.)',
    'STOCK_MOVEMENT': 'Stock movements/shipments',
    'SAMPLES': 'Sample products',
    'STANDS_DISPLAY': 'Stands/display consignments',
    'HOUSE_CONSIGNMENT': 'House consignments',
    'REPAIRS': 'Repair services',
    'DISCOUNT_SPECIALS': 'Special discounts',
    'PROMOTION': 'Promotional items',
    'PROBLEM_ACCOUNT': 'Problem accounts (ZZZ series)',
    'OTHER': 'Other codes'
}

print("\nCategory Definitions:")
for category, definition in category_mapping.items():
    count = len(df[df['REP_CATEGORY'] == category])
    print(f"  {category}: {definition} ({count} records)")