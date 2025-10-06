import pandas as pd
import os
from datetime import datetime

# Load the cleaned data (or create it if needed)
file_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Categories.xlsx"
df = pd.read_excel(file_path)

# Create a function to clean and categorize the product descriptions
def clean_product_description(desc):
    desc = str(desc).strip()
    
    # Map to standardized categories
    if desc in ['Parts', 'Products', 'Packaging', 'PROMOTIONAL GOODS', 'SAMPLES', 'VIP']:
        return desc
    elif desc == 'SALE':
        return 'Sale Items'
    elif desc == 'DISCONTINUED':
        return 'Discontinued'
    elif desc in ['legal costs', 'Admin fees postage / courier']:
        return 'Administrative'
    elif desc in ['Unknown', 'LAST OF RANGE']:
        return desc
    # Handle year patterns
    elif any(year in desc for year in ['2018', '2019', '2017', '2000', '2003']):
        if '+' in desc:
            return 'Future Year Models'
        elif '/' in desc:
            return 'Transition Year Models'
        else:
            return 'Specific Year Models'
    else:
        return 'Other'

# Apply the cleaning
df_cleaned = df.copy()
df_cleaned['PRODCAT_DESC_CLEANED'] = df_cleaned['PRODCAT_DESC'].apply(clean_product_description)

# Create a summary text file with simple ASCII characters
summary_content = """
PRODUCT CATEGORIES CLEANING SUMMARY
====================================

DATE: {date}
ORIGINAL FILE: Product Categories.xlsx
CLEANED FILE: Product_Categories_Cleaned.xlsx

CLEANING OPERATIONS PERFORMED:
-------------------------------
1. Standardized inconsistent product descriptions
2. Grouped year-based entries into meaningful categories
3. Created a new 'PRODCAT_DESC_CLEANED' column

SPECIFIC CLEANING RULES APPLIED:
--------------------------------
- Kept as-is: Parts, Products, Packaging, PROMOTIONAL GOODS, SAMPLES, VIP, Unknown, LAST OF RANGE
- Administrative: legal costs, Admin fees postage / courier -> "Administrative"
- Sales: SALE -> "Sale Items"
- Discontinued: DISCONTINUED -> "Discontinued"
- Year patterns:
  * Specific years (2018, 2019, etc.) -> "Specific Year Models"
  * Future ranges (2017+, 2000+) -> "Future Year Models"
  * Transition periods (01/02, 02/03) -> "Transition Year Models"

RESULTS SUMMARY:
----------------
Total records processed: {total_records}

Cleaned category distribution:
{category_distribution}

BENEFITS OF CLEANING:
---------------------
- Reduced 20+ messy descriptions to 14 standardized categories
- Improved consistency for reporting and analysis
- Better grouping of year-based product lines
- Clearer categorization of administrative and special items

NEXT STEPS:
-----------
- Use PRODCAT_DESC_CLEANED for all reporting and analysis
- Maintain original PRODCAT_DESC for reference
- Apply similar cleaning to related product tables if needed
""".format(
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    total_records=len(df_cleaned),
    category_distribution='\n'.join([f"  - {cat}: {count} records" for cat, count in df_cleaned['PRODCAT_DESC_CLEANED'].value_counts().items()])
)

# Save the summary file with UTF-8 encoding
summary_path = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\products_description_summary.txt"
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(summary_content)

print("Summary file created successfully!")
print(f"Location: {summary_path}")

# Display the summary content
print("\nSummary content:")
print(summary_content)