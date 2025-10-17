from kafka import KafkaProducer
from pymongo import MongoClient
import json
from bson import ObjectId
from datetime import datetime
import time

mongo_uri = "mongodb+srv://powerbi:pbidb4321@cluster0.vlaxs0o.mongodb.net/"
client = MongoClient(mongo_uri)
db = client["clearvue_db"]               
collection = db["purchases"]  

def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  
    if isinstance(obj, ObjectId):
        return str(obj)         
    raise TypeError(f"Type {type(obj)} not serializable")

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v, default=json_serializer).encode('utf-8')
)

print("Producer started — streaming MongoDB data to Kafka...")

for doc in collection.find():
    producer.send("clearvue_stream", value=doc)
    print(f"Sent document: {doc['_id']}")
    time.sleep(1)  # optional, adds small delay for readability

producer.flush()
print("All MongoDB documents sent successfully.")



