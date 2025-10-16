from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'payments',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

print("Consumer started... listening for payment transactions.")

for message in consumer:
    print("Received:", message.value)

"""import json
from kafka import KafkaConsumer
from pymongo import MongoClient

mongo_client = MongoClient("") #mongo uri required
db = mongo_client[""] #required
bi_collection = db[""] #required 

consumer = KafkaConsumer(
    "clearvue_stream",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="clearvue-bi-group",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

print("Listening for messages...")

for message in consumer:
    data = message.value
    print(f"Received: {data}")
    bi_collection.insert_one(data) """

