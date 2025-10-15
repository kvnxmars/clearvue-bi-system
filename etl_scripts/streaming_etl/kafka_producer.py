from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Producer started... sending payment transactions.")

while True:
    payment = {
        "transaction_id": random.randint(1000, 9999),
        "user_id": random.randint(1, 100),
        "amount": round(random.uniform(10.0, 1000.0), 2),
        "status": random.choice(["SUCCESS", "FAILED", "PENDING"])
    }
    producer.send('payments', payment)
    print("Sent:", payment)
    time.sleep(2)
