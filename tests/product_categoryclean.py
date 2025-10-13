import pandas as pd
import json

# Load your enhanced cleaned data
df_enhanced = pd.read_excel(r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\Product_Categories_Enhanced.xlsx")

# Convert to JSON - Method 1: List of dictionaries (perfect for MongoDB)
json_data = df_enhanced.to_dict('records')

# Save as JSON file
with open(r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\product_categories.json", 'w') as f:
    json.dump(json_data, f, indent=2)

print("JSON file created successfully!")
print(f"Total documents: {len(json_data)}")
print("\nSample JSON document:")
print(json.dumps(json_data[0], indent=2))