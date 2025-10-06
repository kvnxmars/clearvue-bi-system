import pandas as pd

# Load all files
categories_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Categories.xlsx"
range_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Ranges.xlsx" 
brands_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Brands.xlsx"

df_categories = pd.read_excel(categories_path)
df_range = pd.read_excel(range_path)
df_brands = pd.read_excel(brands_path)

# =============================================================================
# STEP 1: Clean Product Descriptions
# WHY: Original PRODCAT_DESC has inconsistent entries (years, dates, mixed categories)
# =============================================================================
def clean_product_description(desc):
    desc = str(desc).strip()
    
    # Keep standard categories as-is for consistency
    if desc in ['Parts', 'Products', 'Packaging', 'PROMOTIONAL GOODS', 'SAMPLES', 'VIP']:
        return desc
    elif desc == 'SALE':
        return 'Sale Items'  # Standardize naming
    elif desc == 'DISCONTINUED':
        return 'Discontinued'  # Standardize naming
    elif desc in ['legal costs', 'Admin fees postage / courier']:
        return 'Administrative'  # Group similar administrative items
    elif desc in ['Unknown', 'LAST OF RANGE']:
        return desc  # Keep special categories as-is
    # Group year-based entries for better analysis
    elif any(year in desc for year in ['2018', '2019', '2017', '2000', '2003']):
        if '+' in desc:
            return 'Future Year Models'  # Future model ranges
        elif '/' in desc:
            return 'Transition Year Models'  # Transition periods
        else:
            return 'Specific Year Models'  # Specific year models
    else:
        return 'Other'  # Catch-all for any remaining items

# =============================================================================
# STEP 2: Correct PRAN_CODE Meanings  
# WHY: Investigation revealed the lookup table was wrong - PRAN_CODE 1 and 3 both 
# labeled "Product" but used differently in practice
# =============================================================================
pran_corrections = {
    1: "Parts and Future Models",  # ACTUAL USE: Parts + year models (not "Product")
    2: "Miscellaneous/Administrative",  # ACTUAL USE: Misc items (not just "Parts") 
    3: "Products and Sales"  # ACTUAL USE: Products + sales (not same as PRAN_CODE 1)
}

# =============================================================================
# STEP 3: Create Enhanced DataFrame
# WHY: Preserve original data while adding cleaned/interpreted columns
# =============================================================================
df_enhanced = df_categories.copy()

# Add cleaned product description (NEW COLUMN)
df_enhanced['PRODCAT_DESC_CLEANED'] = df_enhanced['PRODCAT_DESC'].apply(clean_product_description)

# Add corrected PRAN description (NEW COLUMN) 
df_enhanced['PRAN_DESC_CORRECTED'] = df_enhanced['PRAN_CODE'].map(pran_corrections)

# Add brand names for readability (NEW COLUMN)
brand_mapping = dict(zip(df_brands['PRODBRA_CODE'], df_brands['PRODBRA_DESC']))
df_enhanced['BRAND_NAME'] = df_enhanced['BRAND_CODE'].map(brand_mapping)

# =============================================================================
# STEP 4: Save Enhanced File
# WHY: Create a analysis-ready dataset with both original and cleaned data
# =============================================================================
output_path = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\Product_Categories_Enhanced.xlsx"
df_enhanced.to_excel(output_path, index=False)

print("Enhanced cleaned file created successfully!")
print(f"Location: {output_path}")
print(f"Enhanced columns: {df_enhanced.columns.tolist()}")
print(f"Total records: {len(df_enhanced)}")
print("\nSample of enhanced data:")
print(df_enhanced.head(10))

# =============================================================================
# STEP 5: Create Detailed Summary File
# WHY: Document the cleaning logic and data quality issues found
# =============================================================================
summary_content = """
PRODUCT CATEGORIES ENHANCED CLEANING - COMPLETE SUMMARY
========================================================

DATE: {date}
ORIGINAL FILES: 
  - Product Categories.xlsx (main data)
  - Product Ranges.xlsx (lookup - had errors)  
  - Product Brands.xlsx (lookup)

CLEANING OPERATIONS PERFORMED:
------------------------------
1. CLEANED PRODUCT DESCRIPTIONS (PRODCAT_DESC_CLEANED)
   - Standardized inconsistent entries
   - Grouped year-based descriptions into meaningful categories
   - Created consistent naming for sales, administrative items

2. CORRECTED PRAN_CODE MEANINGS (PRAN_DESC_CORRECTED)
   - FIXED DATA QUALITY ISSUE: Original lookup table had PRAN_CODE 1 and 3 both as "Product"
   - Based on actual usage analysis, corrected to:
     * PRAN_CODE 1 -> "Parts and Future Models" 
     * PRAN_CODE 2 -> "Miscellaneous/Administrative"
     * PRAN_CODE 3 -> "Products and Sales"

3. ADDED BRAND NAMES (BRAND_NAME)
   - Replaced BRAND_CODE with actual brand names (A-I) for readability

DATA QUALITY ISSUES IDENTIFIED AND RESOLVED:
--------------------------------------------
1. PRAN_CODE MISLABELING: Lookup table contained incorrect labels that didn't match actual usage
2. INCONSISTENT DESCRIPTIONS: Mixed years, dates, and categories in PRODCAT_DESC
3. DUPLICATE CATEGORIES: Multiple ways to describe similar items

CLEANED CATEGORIES DISTRIBUTION:
--------------------------------
{category_distribution}

CORRECTED PRAN_CODE USAGE:
--------------------------
{pran_distribution}

RECOMMENDATIONS FOR ANALYSIS:
-----------------------------
1. Use PRODCAT_DESC_CLEANED for all reporting (not original PRODCAT_DESC)
2. Use PRAN_DESC_CORRECTED for product range analysis (not original lookup)
3. Use BRAND_NAME for brand-based segmentation
4. All original data preserved for reference if needed

FILE STRUCTURE:
---------------
- All original columns preserved
- Three new columns added:
  * PRODCAT_DESC_CLEANED: Standardized product categories
  * PRAN_DESC_CORRECTED: Corrected product range meanings  
  * BRAND_NAME: Readable brand names
""".format(
    date=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
    category_distribution='\n'.join([f"  - {cat}: {count} records" for cat, count in df_enhanced['PRODCAT_DESC_CLEANED'].value_counts().items()]),
    pran_distribution='\n'.join([f"  - PRAN_CODE {code}: {count} records -> '{desc}'" for code, (desc, count) in enumerate(zip(pran_corrections.values(), df_enhanced['PRAN_CODE'].value_counts().sort_index().values), 1)])
)

# Save summary file
summary_path = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\product_categories_enhanced_summary.txt"
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(summary_content)

print(f"\nDetailed summary created: {summary_path}")
print("\nCleaning complete! Use 'Product_Categories_Enhanced.xlsx' for all future analysis.")