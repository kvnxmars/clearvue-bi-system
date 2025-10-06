import pandas as pd
import os

# Load Excel
file_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Products Styles.xlsx"
df = pd.read_excel(file_path)

print("Original data shape:", df.shape)
print("\nFirst few rows before cleaning:")
print(df.head())

# CLEANING STEPS:

# 1. Standardize all "N/A" values to be consistent
print("\n1. Standardizing N/A values...")
df = df.replace(["N/A", " N/A", "N/A "], "N/A")

# 2. Clean STYLE column - remove extra spaces and standardize fashion/classic format
print("2. Cleaning STYLE column...")
df['STYLE'] = df['STYLE'].str.replace('fashion /classic', 'fashion/classic')
df['STYLE'] = df['STYLE'].str.replace('fashion /classic classic', 'fashion/classic')

# 3. Standardize GENDER values
print("3. Standardizing GENDER values...")
# Ensure all gender values are one of: female, male, unisex, or N/A
valid_genders = ['female', 'male', 'unisex', 'N/A']
df['GENDER'] = df['GENDER'].apply(lambda x: x if x in valid_genders else 'N/A')

# 4. Standardize MATERIAL values
print("4. Standardizing MATERIAL values...")
valid_materials = ['plastic', 'metal', 'titanium', 'combination', 'N/A']
df['MATERIAL'] = df['MATERIAL'].apply(lambda x: x if x in valid_materials else 'N/A')

# 5. Clean BRANDING column
print("5. Standardizing BRANDING values...")
df['BRANDING'] = df['BRANDING'].str.replace('very discreet', 'very_discreet')

# 6. Clean QUAL_PROBS column
print("6. Standardizing QUAL_PROBS values...")
df['QUAL_PROBS'] = df['QUAL_PROBS'].replace(['no problem', 'problem'], ['no_problem', 'problem'])

# 7. Clean INVENTORY_CODE - remove spaces for consistency
print("7. Cleaning INVENTORY_CODE...")
df['INVENTORY_CODE'] = df['INVENTORY_CODE'].astype(str).str.replace(' ', '')

print("\nCleaning completed!")
print("Cleaned data shape:", df.shape)

# Save cleaned file to the cleaned_data folder
cleaned_file_path = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\Products_Styles_Cleaned.xlsx"
df.to_excel(cleaned_file_path, index=False)

print(f"\n✅ Cleaned file saved to: {cleaned_file_path}")

# Show what changed by comparing value counts
print("\n--- GENDER distribution ---")
print("After cleaning:")
print(df['GENDER'].value_counts())

print("\n--- STYLE distribution ---")
print("Top styles after cleaning:")
print(df['STYLE'].value_counts().head(10))

print("\n--- MATERIAL distribution ---")
print(df['MATERIAL'].value_counts())

print("\n--- Sample of cleaned data ---")
print(df[['INVENTORY_CODE', 'GENDER', 'MATERIAL', 'STYLE']].head(10))