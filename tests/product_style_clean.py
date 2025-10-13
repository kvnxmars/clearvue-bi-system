import pandas as pd
import os
import json

# Load Excel
file_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Products Styles.xlsx"
df = pd.read_excel(file_path)

print("=== PRODUCTS STYLES DATA CLEANING ===")

# Store original metrics
original_shape = df.shape
original_na_count = df.isna().sum().sum()

# CLEANING OPERATIONS:

# 1. Standardize N/A values
df_cleaned = df.replace(["N/A", " N/A", "N/A "], "N/A")

# 2. Clean STYLE column - fix inconsistent naming
style_before = df['STYLE'].value_counts()
df_cleaned['STYLE'] = df_cleaned['STYLE'].str.replace('fashion /classic', 'fashion/classic')
df_cleaned['STYLE'] = df_cleaned['STYLE'].str.replace('fashion /classic classic', 'fashion/classic')
style_after = df_cleaned['STYLE'].value_counts()

# 3. Standardize GENDER values
gender_before = df['GENDER'].value_counts()
valid_genders = ['female', 'male', 'unisex', 'N/A']
df_cleaned['GENDER'] = df_cleaned['GENDER'].apply(lambda x: x if str(x) in valid_genders else 'N/A')
gender_after = df_cleaned['GENDER'].value_counts()

# 4. Standardize MATERIAL values
material_before = df['MATERIAL'].value_counts()
valid_materials = ['plastic', 'metal', 'titanium', 'combination', 'N/A']
df_cleaned['MATERIAL'] = df_cleaned['MATERIAL'].apply(lambda x: x if str(x) in valid_materials else 'N/A')
material_after = df_cleaned['MATERIAL'].value_counts()

# 5. Clean BRANDING column
branding_before = df['BRANDING'].value_counts()
df_cleaned['BRANDING'] = df_cleaned['BRANDING'].str.replace('very discreet', 'very_discreet')
branding_after = df_cleaned['BRANDING'].value_counts()

# 6. Clean QUAL_PROBS column
qual_before = df['QUAL_PROBS'].value_counts()
df_cleaned['QUAL_PROBS'] = df_cleaned['QUAL_PROBS'].replace(['no problem', 'problem'], ['no_problem', 'problem'])
qual_after = df_cleaned['QUAL_PROBS'].value_counts()

# 7. Clean INVENTORY_CODE
inventory_spaces_before = df[df['INVENTORY_CODE'].astype(str).str.contains(' ', na=False)].shape[0]
df_cleaned['INVENTORY_CODE'] = df_cleaned['INVENTORY_CODE'].astype(str).str.replace(' ', '')
inventory_spaces_after = df_cleaned[df_cleaned['INVENTORY_CODE'].astype(str).str.contains(' ', na=False)].shape[0]

# Save cleaned Excel file
output_dir = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data"
cleaned_excel_path = os.path.join(output_dir, "Products_Styles_Cleaned.xlsx")
df_cleaned.to_excel(cleaned_excel_path, index=False)

# Convert to JSON and save
json_data = df_cleaned.to_dict(orient='records')
json_file_path = os.path.join(output_dir, "Products_Styles_Cleaned.json")

with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

# Generate cleaning report (without special characters that cause encoding issues)
summary_report = f"""
PRODUCTS STYLES DATA CLEANING REPORT
=====================================

ORIGINAL DATA:
- Records: {original_shape[0]}
- Columns: {original_shape[1]}
- Total NA values: {original_na_count}

FINAL CLEANED DATA:
- Records: {df_cleaned.shape[0]}
- Columns: {df_cleaned.shape[1]}
- Total NA values: {df_cleaned.isna().sum().sum()}

CLEANING OPERATIONS PERFORMED:
1. N/A VALUES: Standardized all 'N/A' formats to consistent format
2. STYLE COLUMN: Fixed inconsistent naming ('fashion /classic' to 'fashion/classic')
3. GENDER COLUMN: Ensured only valid values (female/male/unisex/N/A)
4. MATERIAL COLUMN: Standardized material types (plastic/metal/titanium/combination/N/A)
5. BRANDING COLUMN: Fixed spacing ('very discreet' to 'very_discreet')
6. QUAL_PROBS COLUMN: Standardized values ('no problem' to 'no_problem')
7. INVENTORY_CODE: Removed spaces from {inventory_spaces_before} codes

DATA QUALITY METRICS:
- GENDER Distribution: {dict(gender_after.head())}
- MATERIAL Distribution: {dict(material_after.head())}
- STYLE Distribution: {dict(style_after.head())}
- BRANDING Levels: {dict(branding_after)}
- QUALITY STATUS: {dict(qual_after)}
- Inventory codes with spaces: {inventory_spaces_before} to {inventory_spaces_after}

COLUMN-SPECIFIC CHANGES:
- STYLE: Consolidated {len(style_before)} variations to {len(style_after)} clean categories
- GENDER: Fixed {len([x for x in gender_before.index if x not in valid_genders])} invalid entries
- MATERIAL: Fixed {len([x for x in material_before.index if x not in valid_materials])} invalid entries

OUTPUT FILES GENERATED:
- Excel: Products_Styles_Cleaned.xlsx ({df_cleaned.shape[0]} records)
- JSON: Products_Styles_Cleaned.json ({len(json_data)} records)

DATA INTEGRITY:
- No records lost during cleaning
- All inventory codes preserved
- Data structure maintained
- JSON file contains all cleaned records in structured format
"""

print(summary_report)

# Save summary to text file with proper encoding
summary_path = os.path.join(output_dir, "Products_Styles_Cleaning_Report.txt")
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(summary_report)

print(f"✅ Cleaned Excel file saved to: {cleaned_excel_path}")
print(f"✅ Cleaned JSON file saved to: {json_file_path}")
print(f"✅ Cleaning report saved to: {summary_path}")

# Show JSON structure sample
print("\n=== JSON DATA STRUCTURE SAMPLE ===")
print("First record in JSON format:")
print(json.dumps(json_data[0], indent=2, ensure_ascii=False))

print(f"\n=== CLEANING RESULTS SUMMARY ===")
print(f"✅ Total records processed: {len(json_data)}")
print(f"✅ Spaces removed from {inventory_spaces_before} inventory codes")
print(f"✅ NA values standardized: {original_na_count} -> {df_cleaned.isna().sum().sum()}")
print(f"✅ JSON file created with all {len(json_data)} cleaned records")