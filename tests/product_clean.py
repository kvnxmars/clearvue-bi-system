import pandas as pd
import os
import json
from datetime import datetime

def convert_cleaned_data_to_json():
    """Convert the actual cleaned Excel data to JSON format"""
    
    # Path to your cleaned Excel file
    cleaned_excel_path = r"C:\Users\ibrah\Music\clearvue-bi-system\raw_data\Products_cleaned.xlsx"
    
    # Read the cleaned data
    df_cleaned = pd.read_excel(cleaned_excel_path)
    
    print(f"📊 Converting cleaned data to JSON...")
    print(f"Records: {len(df_cleaned):,}")
    print(f"Columns: {len(df_cleaned.columns)}")
    print(f"Columns: {list(df_cleaned.columns)}")
    
    # Convert to JSON - Choose ONE of these formats:
    
    # OPTION 1: Records format (most common)
    json_data_records = df_cleaned.to_dict('records')
    
    # OPTION 2: Split format (metadata + data)
    json_data_structured = {
        "metadata": {
            "dataset": "Products Data",
            "export_date": datetime.now().isoformat(),
            "total_records": len(df_cleaned),
            "total_columns": len(df_cleaned.columns),
            "columns": df_cleaned.columns.tolist()
        },
        "data": json_data_records
    }
    
    # Save both formats
    output_dir = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as simple records format
    records_path = os.path.join(output_dir, "products_data_records.json")
    with open(records_path, 'w', encoding='utf-8') as f:
        json.dump(json_data_records, f, indent=2)
    
    # Save as structured format
    structured_path = os.path.join(output_dir, "products_data_structured.json")
    with open(structured_path, 'w', encoding='utf-8') as f:
        json.dump(json_data_structured, f, indent=2)
    
    print(f"✅ Cleaned data converted to JSON!")
    print(f"📁 Records format: {records_path}")
    print(f"📁 Structured format: {structured_path}")
    print(f"📊 Sample of first record:")
    print(json.dumps(json_data_records[0], indent=2))
    
    return json_data_structured

# Run the conversion
if __name__ == "__main__":
    convert_cleaned_data_to_json()