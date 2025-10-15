from kafka import KafkaProducer
import json
import time

# Setup Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("🚀 Streaming Enhanced Product Data to Kafka...")
print("=" * 50)

try:
    # Load your enhanced data
    with open('cleaned_data/Product_Categories_Enhanced.xlsx', 'r') as f:
        # If it's Excel, we need pandas
        import pandas as pd
        df = pd.read_excel('cleaned_data/Product_Categories_Enhanced.xlsx')
        enhanced_products = df.to_dict('records')
    
    print(f"📊 Loaded {len(enhanced_products)} enhanced product records")
    
    # Stream to Kafka
    for i, product in enumerate(enhanced_products):
        # Add streaming metadata
        product['stream_timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        product['stream_batch'] = 'enhanced_data'
        
        # Send to Kafka
        producer.send('clearvue-products-enhanced', product)
        print(f"✅ [{i+1}/{len(enhanced_products)}] Streamed: {product['PRODCAT_CODE']} - {product['PRODCAT_DESC_CLEANED']}")
        
        # Small delay to see the streaming effect
        time.sleep(0.5)
    
    producer.flush()
    print("=" * 50)
    print(f"🎉 Successfully streamed {len(enhanced_products)} enhanced products!")
    print("   Topics: clearvue-products-enhanced")
    print("   Includes: Cleaned descriptions + Corrected PRAN codes + Brand names")
    
except FileNotFoundError:
    print("❌ Enhanced file not found. Let's check what files exist...")
    import os
    print("Files in cleaned_data/:")
    for file in os.listdir('cleaned_data'):
        print(f"   - {file}")

except Exception as e:
    print(f"❌ Error: {e}")