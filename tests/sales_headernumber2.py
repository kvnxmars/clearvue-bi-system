import pandas as pd
import os
import json

def convert_cleaned_data_to_json():
    """Convert the actual cleaned Sales Header data to JSON format"""
    
    # Path to your cleaned Excel file
    cleaned_excel_path = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\Sales_Header_Cleaned.xlsx"
    
    # Read the cleaned data
    df_cleaned = pd.read_excel(cleaned_excel_path)
    
    print(f"📊 Converting cleaned data to JSON...")
    print(f"Records: {len(df_cleaned):,}")
    
    # NUCLEAR OPTION: Convert everything to basic Python types
    json_data_records = []
    for _, row in df_cleaned.iterrows():
        record = {}
        for col in df_cleaned.columns:
            value = row[col]
            # Convert to basic Python types
            if pd.isna(value):
                record[col] = None
            elif hasattr(value, 'item'):  # numpy types
                record[col] = value.item()
            else:
                record[col] = str(value)
        json_data_records.append(record)
    
    # Save the main data file
    output_dir = r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data"
    os.makedirs(output_dir, exist_ok=True)
    
    records_path = os.path.join(output_dir, "sales_data_records.json")
    with open(records_path, 'w', encoding='utf-8') as f:
        json.dump(json_data_records, f, indent=2, ensure_ascii=False)
    
    print(f"✅ SUCCESS! JSON file created!")
    print(f"📁 Location: {records_path}")
    print(f"📊 Records: {len(json_data_records):,}")
    
    return json_data_records

# Run the conversion
if __name__ == "__main__":
    convert_cleaned_data_to_json()