import pymongo
from pymongo import MongoClient
import json

# MongoDB connection details
MONGODB_URI = "mongodb+srv://powerbi:pbidb4321@cluster0.vlaxs0o.mongodb.net/"
DATABASE_NAME = "clearvue_bi_system"
COLLECTION_NAME = "finance"

def connect_to_mongodb():
    """Connect to MongoDB and return client and collection"""
    try:
        client = MongoClient(MONGODB_URI)
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        return client, collection
    except Exception as e:
        print(f"Connection failed: {e}")
        return None, None

def get_mongodb_stats(collection):
    """Get database statistics"""
    try:
        count = collection.count_documents({})
        print(f"Total documents in collection: {count}")
        
        # Sample a document to show structure
        sample = collection.find_one()
        if sample:
            print("Sample document structure:")
            print(json.dumps(sample, indent=2, default=str))
        return count
    except Exception as e:
        print(f"Could not get stats: {e}")
        return 0

# Main execution
print("=== MONGODB STREAMING TEST ===")
print("🔌 Connecting to MongoDB...")

# Connect to MongoDB
client, collection = connect_to_mongodb()

if client is not None and collection is not None:
    # Get current database stats
    print("\n--- Current Database Status ---")
    get_mongodb_stats(collection)
    
    client.close()



        