import pandas as pd

# Load all three files with correct names
categories_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Categories.xlsx"
range_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Ranges.xlsx" 
brands_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Product Brands.xlsx"

df_categories = pd.read_excel(categories_path)
df_range = pd.read_excel(range_path)
df_brands = pd.read_excel(brands_path)

print("=== PRAN_CODE INVESTIGATION ===")
print("\n1. PRODUCT RANGES LOOKUP TABLE:")
print(df_range)
print(f"\nUnique PRAN_DESC values: {df_range['PRAN_DESC'].unique()}")

print("\n2. HOW PRAN_CODES ARE ACTUALLY USED IN PRODUCT CATEGORIES:")
pran_usage = df_categories.groupby('PRAN_CODE')['PRODCAT_DESC'].agg(['count', lambda x: list(x.unique())])
pran_usage.columns = ['count', 'unique_descriptions']
print(pran_usage)

print("\n3. CROSS-REFERENCE: PRAN_CODE vs PRODCAT_DESC PATTERNS:")
for pran_code in sorted(df_categories['PRAN_CODE'].unique()):
    subset = df_categories[df_categories['PRAN_CODE'] == pran_code]
    official_label = df_range[df_range['PRAN_CODE'] == pran_code]['PRAN_DESC'].iloc[0] if pran_code in df_range['PRAN_CODE'].values else 'NOT FOUND'
    print(f"\nPRAN_CODE {pran_code} ({official_label}):")
    print(f"  Count: {len(subset)}")
    print(f"  PRODCAT_DESC values: {subset['PRODCAT_DESC'].unique().tolist()}")
    print(f"  Most common: {subset['PRODCAT_DESC'].mode().iloc[0] if len(subset) > 0 else 'N/A'}")

print("\n4. BRAND CODES USED WITH EACH PRAN_CODE:")
brand_pran_analysis = df_categories.groupby(['PRAN_CODE', 'BRAND_CODE']).size().reset_index(name='count')
print(brand_pran_analysis)

print("\n5. DETECTING THE PATTERN - What each PRAN_CODE actually represents:")
# Let's see if there's a logical pattern based on actual usage
pattern_analysis = []
for pran_code in [1, 2, 3]:
    subset = df_categories[df_categories['PRAN_CODE'] == pran_code]
    if len(subset) > 0:
        desc_pattern = subset['PRODCAT_DESC'].mode().iloc[0]
        official_label = df_range[df_range['PRAN_CODE'] == pran_code]['PRAN_DESC'].iloc[0] if pran_code in df_range['PRAN_CODE'].values else 'NOT FOUND'
        pattern_analysis.append({
            'PRAN_CODE': pran_code,
            'Official_Label': official_label,
            'Actual_Primary_Use': desc_pattern,
            'Record_Count': len(subset),
            'All_Used_Descriptions': subset['PRODCAT_DESC'].unique().tolist()
        })

pattern_df = pd.DataFrame(pattern_analysis)
print(pattern_df[['PRAN_CODE', 'Official_Label', 'Actual_Primary_Use', 'Record_Count']])

print("\n6. BRAND NAMES FOR CONTEXT:")
print(df_brands)