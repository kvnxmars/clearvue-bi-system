import os
DATA_DIR = os.path.join("..", "raw_data")
files = ["Suppliers.xlsx", "Purchases Headers.xlsx", "Purchases Lines.xlsx"]
for file in files:
    path = os.path.join(DATA_DIR, file)