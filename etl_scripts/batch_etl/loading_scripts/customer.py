"""
=============================================================================
MONGODB ATLAS UPLOAD SCRIPT
Load Customer Collection JSON into MongoDB Atlas
=============================================================================
"""

import json
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, BulkWriteError
from pathlib import Path

# ============================================================================
# 0. CONFIGURATION
# ============================================================================

print("\n" + "="*80)
print("MONGODB ATLAS UPLOAD - INITIALIZATION")
print("="*80 + "\n")

# TODO: REPLACE WITH YOUR MONGODB ATLAS CONNECTION STRING
# Format: mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_URI = "mongodb+srv://GenericUser:PDgI9F4KjSvPqFLJ@cluster0.vlaxs0o.mongodb.net/"

# TODO: Set your database and collection names
DATABASE_NAME = "clearvue_bi_system"
COLLECTION_NAME = "customer"

# Path to your exported JSON file
json_file_path = Path(__file__).parent.parent / "customer_collection.json"

print(f"Connection string: {MONGODB_URI}")
print(f"Database: {DATABASE_NAME}")
print(f"Collection: {COLLECTION_NAME}")
print(f"JSON file: {json_file_path}\n")


# ============================================================================
# 1. VALIDATE JSON FILE EXISTS
# ============================================================================

print("PHASE 1: VALIDATING JSON FILE")
print("-" * 80)

if not json_file_path.exists():
    print(f"✗ JSON file not found at: {json_file_path}")
    print("Please make sure customer_collection.json exists in the parent directory")
    raise FileNotFoundError(f"File not found: {json_file_path}")

print(f"✓ Found JSON file: {json_file_path}")
file_size_mb = json_file_path.stat().st_size / (1024 * 1024)
print(f"  File size: {file_size_mb:.2f} MB\n")


# ============================================================================
# 2. LOAD AND VALIDATE JSON DATA
# ============================================================================

print("PHASE 2: LOADING JSON DATA")
print("-" * 80)

try:
    with open(json_file_path, "r") as f:
        customer_data = json.load(f)
    
    if not isinstance(customer_data, list):
        print("✗ JSON file must contain a list of documents")
        raise ValueError("Invalid JSON structure - expected list of objects")
    
    print(f"✓ Successfully loaded JSON file")
    print(f"  Total documents: {len(customer_data)}")
    
    # Validate document structure
    if len(customer_data) > 0:
        sample_doc = customer_data[0]
        required_fields = ["_id", "customer_categories", "region"]
        missing_fields = [f for f in required_fields if f not in sample_doc]
        
        if missing_fields:
            print(f"⚠ WARNING: Sample document missing fields: {missing_fields}")
        else:
            print(f"✓ Sample document structure valid")
    
    print()
    
except json.JSONDecodeError as e:
    print(f"✗ JSON parsing error: {e}")
    raise
except Exception as e:
    print(f"✗ Error loading JSON: {e}")
    raise


# ============================================================================
# 3. CONNECT TO MONGODB ATLAS
# ============================================================================

print("PHASE 3: CONNECTING TO MONGODB ATLAS")
print("-" * 80)

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    
    # Test the connection
    client.admin.command('ping')
    print("✓ Successfully connected to MongoDB Atlas")
    
    # Access database and collection
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    print(f"✓ Accessed database: {DATABASE_NAME}")
    print(f"✓ Accessed collection: {COLLECTION_NAME}\n")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check your connection string is correct")
    print("2. Verify username and password")
    print("3. Check IP whitelist in MongoDB Atlas (add your IP or 0.0.0.0)")
    print("4. Ensure your network allows outbound connections on port 27017")
    raise


# ============================================================================
# 4. CHECK EXISTING DATA
# ============================================================================

print("PHASE 4: CHECKING EXISTING DATA")
print("-" * 80)

try:
    existing_count = collection.count_documents({})
    print(f"Existing documents in collection: {existing_count}")
    
    if existing_count > 0:
        print(f"⚠ WARNING: Collection is not empty")
        user_input = input("Do you want to (1) Replace all data, (2) Skip duplicates, (3) Cancel? [1/2/3]: ").strip()
        
        if user_input == "1":
            print("  Action: Clearing collection...")
            collection.delete_many({})
            print("  ✓ Collection cleared")
        elif user_input == "3":
            print("  Cancelled by user")
            raise KeyboardInterrupt("User cancelled upload")
        else:
            print("  Action: Will skip duplicate IDs\n")
    
except Exception as e:
    print(f"✗ Error checking existing data: {e}")
    raise

print()


# ============================================================================
# 5. UPLOAD DOCUMENTS TO MONGODB
# ============================================================================

print("PHASE 5: UPLOADING DOCUMENTS")
print("-" * 80)

try:
    # Option 1: Insert all documents (will fail on duplicates)
    result = collection.insert_many(customer_data, ordered=False)
    
    print(f"✓ Successfully inserted {len(result.inserted_ids)} documents")
    
except BulkWriteError as e:
    # Some documents may have been inserted despite errors
    print(f"⚠ Bulk write error (some documents may have been inserted)")
    print(f"  Details: {e.details}")
    inserted_count = e.details.get("nInserted", 0)
    print(f"  Documents inserted: {inserted_count}")
    
except DuplicateKeyError as e:
    print(f"✗ Duplicate key error: {e}")
    print("  Hint: Some documents with the same _id already exist")
    raise

except Exception as e:
    print(f"✗ Upload failed: {e}")
    raise

print()


# ============================================================================
# 6. VERIFY UPLOAD
# ============================================================================

print("PHASE 6: VERIFYING UPLOAD")
print("-" * 80)

try:
    total_in_db = collection.count_documents({})
    print(f"Total documents in collection: {total_in_db}")
    
    # Check collection statistics
    stats = db.command("collStats", COLLECTION_NAME)
    avg_doc_size = stats.get("avgObjSize", 0)
    print(f"Average document size: {avg_doc_size / 1024:.2f} KB")
    
    # Verify indexes
    indexes = collection.list_indexes()
    print(f"Indexes on collection: {len(list(indexes))}")
    
    # Sample a few documents
    print(f"\nSample documents from collection:")
    samples = list(collection.find().limit(3))
    for i, doc in enumerate(samples):
        print(f"\n  Sample {i + 1}:")
        print(f"    _id: {doc.get('_id')}")
        print(f"    customer_categories: {doc.get('customer_categories')}")
        print(f"    region: {doc.get('region')}")
    
    print()
    
except Exception as e:
    print(f"✗ Verification failed: {e}")
    raise


# ============================================================================
# 7. CREATE INDEXES (OPTIONAL)
# ============================================================================

print("PHASE 7: CREATING INDEXES")
print("-" * 80)

try:
    # TODO: Create indexes on frequently queried fields for performance
    # Index on CCAT_CODE for category queries
    if "customer_categories.ccat_code" in str(collection.find_one()):
        collection.create_index("customer_categories.ccat_code")
        print("✓ Created index on customer_categories.ccat_code")
    
    # Index on REGION_CODE for region queries
    if "region.region_code" in str(collection.find_one()):
        collection.create_index("region.region_code")
        print("✓ Created index on region.region_code")
    
    # Index on REP_CODE for sales rep queries
    if "rep_code" in str(collection.find_one()):
        collection.create_index("rep_code")
        print("✓ Created index on rep_code")
    
    print()
    
except Exception as e:
    print(f"⚠ Warning: Could not create indexes: {e}")
    print("  This is not critical - you can create them manually in MongoDB Atlas\n")


# ============================================================================
# 8. CLOSE CONNECTION & SUMMARY
# ============================================================================

print("PHASE 8: CLOSING CONNECTION")
print("-" * 80)

try:
    client.close()
    print("✓ Closed MongoDB connection\n")
except Exception as e:
    print(f"⚠ Warning: Error closing connection: {e}\n")


print("="*80)
print("✓ CUSTOMER COLLECTION UPLOAD COMPLETE")
print("="*80)
print(f"\nSummary:")
print(f"  Database: {DATABASE_NAME}")
print(f"  Collection: {COLLECTION_NAME}")
print(f"  Documents uploaded: {total_in_db}")
print(f"  Connection: MongoDB Atlas")
print("\n")