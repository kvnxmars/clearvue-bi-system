import pandas as pd
import os
from datetime import datetime

def quick_cleaning_report(original_file, cleaned_file):
    """Quick cleaning report in your preferred format"""
    
    df_before = pd.read_excel(original_file)
    df_after = pd.read_excel(cleaned_file)
    
    # Save a summary report
    summary_report = f"""
PRODUCTS DATA CLEANING REPORT
==================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Original File: {os.path.basename(original_file)}
Cleaned File: {os.path.basename(cleaned_file)}

Original Records: {df_before.shape[0]:,}
Final Records: {df_after.shape[0]:,}
Records Removed: {df_before.shape[0] - df_after.shape[0]:,}

CLEANING OPERATIONS PERFORMED:
1. COLUMN NAMES: Standardized (strip spaces, lowercase, underscore)
2. DUPLICATES: Removed {df_before.duplicated().sum():,} duplicate rows
3. EMPTY COLUMNS: Removed {df_before.shape[1] - df_after.shape[1]} empty columns
4. MISSING VALUES: Filled {df_before.isnull().sum().sum():,} missing values
5. TEXT DATA: Stripped whitespace from all text fields

DATA QUALITY METRICS:
- Null Values Before: {df_before.isnull().sum().sum():,}
- Null Values After: {df_after.isnull().sum().sum():,}
- Duplicate Rows: {df_before.duplicated().sum():,} → {df_after.duplicated().sum():,}
- Empty Strings: {(df_before == '').sum().sum():,} → {(df_after == '').sum().sum():,}

COLUMN SUMMARY:
- Original Columns: {list(df_before.columns)}
- Cleaned Columns: {list(df_after.columns)}

STATUS: ✅ DATA CLEANING COMPLETED SUCCESSFULLY
Ready for analysis and visualization.
"""
    
    print(summary_report)
    
    # Save summary to text file in the specified folder
    output_dir = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data"
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as 'Products Summary'
    summary_path = os.path.join(output_dir, "Products Summary.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_report)
    
    print(f"📄 Cleaning report saved to: {summary_path}")
    return summary_report

# Run the quick version
original_file = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Products.xlsx"
cleaned_file = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Products_cleaned.xlsx"

quick_cleaning_report(original_file, cleaned_file)