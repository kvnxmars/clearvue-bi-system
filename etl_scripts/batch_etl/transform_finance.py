import pandas as pd 
import json
from pathlib import Path

#helper function to load excel files
def load_and_sanitize(file_name, sheet_name="None"):
    df = pd.read_excel(raw_data_dir/file_name, sheet_name=sheet_name)
    #**strip all whitespace and standardise to uppercase
    df.columns = df.columns.str.strip().str.upper()
    return df



print ("\n---1.1 FINANCE DATA CLEANSING & MERGING ---")

# --- Load and clean individual files ---

# Get the directory containing the script
print("getting the directory with script..")
script_dir = Path(__file__).parent

# Navigate two levels up, then into raw_data
raw_data_dir = script_dir / ".." / ".." / "raw_data"

# Or use parent property (cleaner)
raw_data_dir = script_dir.parent.parent / "raw_data"

print("Cleaning the payment header and lines..")
#1. payment header - deduplication && sanitising data
payment_header = pd.read_excel(raw_data_dir/"Payment Header.xlsx",sheet_name="Payment_Header")
payment_header = load_and_sanitize("Payment Header.xlsx", "Payment_Header")
payment_header = payment_header.drop_duplicates()



#2. Payment lines (data type fixes, deduplication and removing missing values)
payment_lines = pd.read_excel(raw_data_dir/"Payment Lines.xlsx",sheet_name="Payment_Lines")
payment_lines = load_and_sanitize("Payment Lines.xlsx", "Payment_Lines")
print("Payment lines columns:", payment_lines.columns.tolist())

# AGGRESSIVE FIX: Explicitly rename the customer column after cleaning.
# If the column exists, it should now be named 'CUSTOMER_NUMBER'.
# Note: If the actual column name is something totally different (like 'CUSTID'), 
# you would replace 'CUSTOMER_NUMBER' in the .columns property below with the true name.
if 'CUSTOMER_NUMBER' not in payment_lines.columns:
    print("!! WARNING: CUSTOMER_NUMBER not found in Payment Lines. Check original file.")

payment_lines["DEPOSIT_DATE"] = pd.to_datetime(payment_lines["DEPOSIT_DATE"], errors="coerce")

missing_summary = payment_lines.isnull().sum()


amount_cols_pl = ["BANK_AMT", "DISCOUNT", "TOT_PAYMENT"]
for col in amount_cols_pl:
    #convert bad values with nan
    payment_lines[col] = pd.to_numeric(payment_lines[col], errors="coerce")
payment_lines = payment_lines.drop_duplicates()

# remove rows with missing deposit reference or customer number
payment_lines = payment_lines.dropna(subset=["CUSTOMER_NUMBER", "DEPOSIT_REF"])

if "FIN_PERIOD" not in payment_lines.columns and "DEPOSIT_DATE" in payment_lines.columns:
    payment_lines["FIN_PERIOD"] = pd.to_datetime(payment_lines["DEPOSIT_DATE"], errors="coerce").dt.strftime("%Y%m").astype(int)



#3. Age analysis

print("Cleaning age analysis..")
#Cleaning Age_Analysis
age_df = pd.read_excel(raw_data_dir/"Age Analysis.xlsx", sheet_name="Age_Analysis")
age_df = load_and_sanitize("Age Analysis.xlsx", "Age_Analysis")
#--sanitize column names to remove whitespace
age_df.columns = age_df.columns.str.strip().str.upper()
print("Age analysis columns:", age_df.columns.tolist())

# AGGRESSIVE FIX: Ensure the age analysis customer column is named 'CUSTOMER_NUMBER'.
if 'CUSTOMER_NUMBER' not in age_df.columns:
    print("!! WARNING: CUSTOMER_NUMBER not found in Age Analysis. Check original file.")


# Remove duplicates
age_df = age_df.drop_duplicates()

# Ensure numeric columns are actually numeric
amount_cols = [col for col in age_df.columns if col.startswith("AMT_") or col == "TOTAL_DUE"]
age_df[amount_cols] = age_df[amount_cols].apply(pd.to_numeric, errors="coerce")

# Fill missing values with 0 for amounts
age_df[amount_cols] = age_df[amount_cols].fillna(0)

# Check consistency of totals
age_df["BUCKET_SUM"] = age_df[amount_cols].drop("TOTAL_DUE", axis=1).sum(axis=1)
age_df["CONSISTENT_PAYMENTS"] = age_df["TOTAL_DUE"].round(2) == age_df["BUCKET_SUM"].round(2)



#Cleaning Customer Account Parameters
print("Cleaning account parameters..")
custAcc_df = pd.read_excel(raw_data_dir/"Customer Account Parameters.xlsx", sheet_name="Customer_Account_Parameters")

# Remove duplicates
custAcc_df = custAcc_df.drop_duplicates()
# Drop rows with missing values in key columns
custAcc_df = custAcc_df.dropna(subset=["CUSTOMER_NUMBER", "PARAMETER"])

# Standardize text 
custAcc_df["CUSTOMER_NUMBER"] = custAcc_df["CUSTOMER_NUMBER"].astype(str).str.strip()
custAcc_df["PARAMETER"] = custAcc_df["PARAMETER"].str.strip().str.capitalize()

print("Payment header shape(whatevr that means): ",payment_header.shape)
print("Payment line shape(whatevr that means): ",payment_lines.shape)
print("Age dataframe shape(whatevr that means): ",age_df.shape)
print("Customer Account params shape(whatevr that means): ",custAcc_df.shape)

# --- STANDARDIZE CUSTOMER_NUMBER ACROSS ALL DATAFRAMES ---
for df_name, df in [("payment_lines", payment_lines), ("age_df", age_df), ("custAcc_df", custAcc_df)]:
    if "CUSTOMER_NUMBER" in df.columns:
        df["CUSTOMER_NUMBER"] = (
            df["CUSTOMER_NUMBER"]
            .astype(str)
            .str.strip()              # remove whitespace
            .str.replace("'", "", regex=False)  # remove stray quotes
            .str.upper()              # uppercase consistency
        )
        print(f"Standardized CUSTOMER_NUMBER in {df_name}, sample:", df["CUSTOMER_NUMBER"].head(3).tolist())

#DEBUGGING BEFORE MERGE

# Check uniqueness of merge keys
print("Unique deposit refs in payment_lines:", payment_lines['DEPOSIT_REF'].nunique())
print("Unique deposit refs in payment_header:", payment_header['DEPOSIT_REF'].nunique())

print("Unique customer numbers in payment_lines:", payment_lines['CUSTOMER_NUMBER'].nunique())
print("Unique customer numbers in age_df:", age_df['CUSTOMER_NUMBER'].nunique())

# --- Debug: find common and missing customers ---
pl_customers = set(payment_lines["CUSTOMER_NUMBER"].unique())
aa_customers = set(age_df["CUSTOMER_NUMBER"].unique())

common_customers = pl_customers.intersection(aa_customers)
only_in_pl = pl_customers - aa_customers
only_in_aa = aa_customers - pl_customers

print(f"Total customers in payments: {len(pl_customers)}")
print(f"Total customers in age analysis: {len(aa_customers)}")
print(f"Common customers: {len(common_customers)}")

# Print a few examples of what doesn't overlap
print("\nSample in payments only:", list(only_in_pl)[:10])
print("Sample in age analysis only:", list(only_in_aa)[:10])

print("\n🔍 Payment sample CUSTOMER_NUMBERs:", payment_lines["CUSTOMER_NUMBER"].unique()[:10])
print("🔍 Age sample CUSTOMER_NUMBERs:", age_df["CUSTOMER_NUMBER"].unique()[:10])

# check intersection
common_customers = set(payment_lines["CUSTOMER_NUMBER"]) & set(age_df["CUSTOMER_NUMBER"])
print("🔍 Common customers count:", len(common_customers))
print("🔍 Sample common customers:", list(common_customers)[:10])


# --- MERGING PROCESS ---
# Clean up duplicate columns

# --- 1️⃣ Aggregate Payment Lines into Nested Lists ---
print("step 1: aggregating payment lines into nested list..")
payment_lines_nested = (
    payment_lines.groupby(["CUSTOMER_NUMBER", "FIN_PERIOD"], as_index=False)
    .apply(
        lambda g: pd.Series({
            "payment_lines": g[["DEPOSIT_DATE", "DEPOSIT_REF", "BANK_AMT", "DISCOUNT"]]
        }),
        include_groups=False
    )

)
print(f"  ✓ {len(payment_lines_nested)} payment line groups created\n")


# --- 2️⃣ Aggregate Age Analysis (Totals and Buckets) ---
print("step 2: Aggregating age analysis by customer (nesting FIN_PERIODS)...")
age_cols = [c for c in age_df.columns if c.startswith("AMT")]

# Create a dictionary of days due amounts
age_df["days_due"] = age_df[age_cols].apply(
    lambda r: {
        c.replace("AMT_", "").replace("_DAYS", "").replace("CURRENT", "0"): int(v)
               for c, v in r.items() 
               if v !=0
    }, 
    axis=1
)

#select only relevant columns for merging
age_slim = age_df[["CUSTOMER_NUMBER", "FIN_PERIOD", "TOTAL_DUE", "AMT_CURRENT", "days_due"]].copy()
print(f"  ✓ {len(age_slim)} age analysis records ready for merging\n")

#merge age analysis with payment lines
print("Step 3: Merging age analysis with payment lines..")
finance_data = (
    age_slim
    .merge(payment_lines_nested,
           on=["CUSTOMER_NUMBER", "FIN_PERIOD"],
           how="left")
)

# Fill missing payment_lines with empty list
finance_data["payment_lines"] = finance_data["payment_lines"].apply(
    lambda x: x if isinstance(x, list) else []
)

print(f"  ✓ Merged: {len(finance_data)} finance records\n")

print("Sample merged finance data:", finance_data.head(3))


# --- 3️⃣  Attach Customer Parameters---
print("step 4: attaching customer parameters..")
cust_params_grouped = (
    custAcc_df.groupby("CUSTOMER_NUMBER", as_index=False)["PARAMETER"]
    .apply(list, include_groups = False)
    .reset_index()
    .rename(columns={"PARAMETER": "ACCOUNT_PARAMETERS"})
)

finance_data = finance_data.merge(cust_params_grouped, on="CUSTOMER_NUMBER", how="left")
finance_data["ACCOUNT_PARAMETERS"] = finance_data["ACCOUNT_PARAMETERS"].apply(
    lambda x: x if  isinstance(x, list) else [] #replace NaN with empty list
)
print(f"  ✓ Attached account parameters, total records now: {len(finance_data)}\n")


# --- 5️⃣ Verify Payment Lines ---
records_with_payments = finance_data[finance_data["payment_lines"].apply(len) > 0]
print(f"Records with payment data: {len(records_with_payments)} / {len(finance_data)}")
if len(records_with_payments) > 0:
    sample_row = records_with_payments.iloc[0]
    print(f"  Example: {sample_row['CUSTOMER_NUMBER']} period {sample_row['FIN_PERIOD']} has {len(sample_row['payment_lines'])} payment(s)\n")



# --- 6️⃣ Build Final Finance Collection Documents ---
print("STep 5: Building final FINANCE collection documents..")

finance_collection = []
for _, row in finance_data.iterrows():
    doc = {
        "_id": f"{row['CUSTOMER_NUMBER']}_{row['FIN_PERIOD']}",
        "customer_number": row["CUSTOMER_NUMBER"],
        "fin_period": str(int(row["FIN_PERIOD"])) if pd.notna(row["FIN_PERIOD"]) else None,
        "total_due": float(row["TOTAL_DUE"]) if pd.notna(row["TOTAL_DUE"]) else 0.0,
        "amt_current": float(row["AMT_CURRENT"]) if pd.notna(row["AMT_CURRENT"]) else 0.0,
        "days_due": row["days_due"] if isinstance(row["days_due"], dict) else {},
        "payment_lines": row["payment_lines"] if isinstance(row["payment_lines"], list) else [],
        "account_parameters": row["ACCOUNT_PARAMETERS"] if isinstance(row["ACCOUNT_PARAMETERS"], list) else []
    }
    finance_collection.append(doc)

print(f" ✓ Build {len(finance_collection)} finance documents for MongoDB\n")

# --- EXPORT TO JSON FOR INSPECTION ---
print ("Step 6: Exporting to JSON for inspection..")
output_file = raw_data_dir.parent / "finance_collection.json"

try:
    with open(output_file, "w") as f:
        json.dump(finance_collection, f, indent=2)
    print(f"  ✓ Exported finance collection to {output_file}\n")

    #statistics
    print("===EXPORT SUMMARY===")
    print(f"Total documents: {len(finance_collection)}")
    print(f"File size: {output_file.stat().st_size / 1024:.2f} KB\n")

    if finance_collection:
        print ("Sample FINANCE document:")
        print(json.dumps(finance_collection[0], indent=2))

except Exception as e:
    print(f"\n[FAILURE] Could not export finance collection: {e}")
    raise

print("Finance collection build complete.\n")



#end of script