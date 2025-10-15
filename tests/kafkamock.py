import json
import time
from datetime import datetime
import os

class MockKafka:
    """Fake Kafka that works instantly - no installation needed"""
    
    def __init__(self):
        self.topics = {
            'clearvue-products': [],
            'clearvue-sales': [],
            'clearvue-customers': []
        }
        print("🚀 MOCK KAFKA - Ready instantly!")
    
    def send(self, topic, message):
        """Simulate sending to Kafka"""
        message['kafka_timestamp'] = datetime.now().isoformat()
        self.topics[topic].append(message)
        print(f"📤 [MOCK] Sent to {topic}: {message.get('PRODCAT_CODE', 'Unknown')}")
        return True
    
    def consume(self, topic, limit=5):
        """Simulate consuming from Kafka"""
        print(f"📥 [MOCK] Consuming from {topic}...")
        messages = self.topics[topic][:limit]
        
        for i, msg in enumerate(messages):
            print(f"   📨 Message {i+1}:")
            if 'PRODCAT_CODE' in msg:
                print(f"      Product: {msg['PRODCAT_CODE']} - {msg['PRODCAT_DESC_CLEANED']}")
                print(f"      Brand: {msg['BRAND_NAME']} | Range: {msg['PRAN_DESC_CORRECTED']}")
            else:
                print(f"      Data: {msg}")
            print(f"      Time: {msg['kafka_timestamp']}")
            time.sleep(0.5)
        
        return messages

class ClearVueMockPipeline:
    def __init__(self):
        self.kafka = MockKafka()
    
    def stream_all_data(self):
        """Stream all your cleaned data through mock Kafka"""
        
        # 1. Stream Product Data
        print("\n" + "="*50)
        print("📦 STREAMING PRODUCT DATA")
        print("="*50)
        
        try:
            with open(r"C:\Users\ibrah\Music\clearvue-bi-system\cleaned_data\product_categories.json", 'r') as f:
                products = json.load(f)
            
            for i, product in enumerate(products[:8]):  # First 8 products
                self.kafka.send('clearvue-products', product)
                time.sleep(0.3)  # Simulate real-time
                
        except FileNotFoundError:
            print("❌ product_categories.json not found - creating sample data...")
            # Create sample data if file doesn't exist
            sample_products = [
                {'PRODCAT_CODE': '001', 'PRODCAT_DESC_CLEANED': 'Parts', 'BRAND_NAME': 'A', 'PRAN_DESC_CORRECTED': 'Parts and Models'},
                {'PRODCAT_CODE': '002', 'PRODCAT_DESC_CLEANED': 'Products', 'BRAND_NAME': 'B', 'PRAN_DESC_CORRECTED': 'Products and Sales'},
                {'PRODCAT_CODE': '003', 'PRODCAT_DESC_CLEANED': 'Sale Items', 'BRAND_NAME': 'C', 'PRAN_DESC_CORRECTED': 'Products and Sales'}
            ]
            for product in sample_products:
                self.kafka.send('clearvue-products', product)
                time.sleep(0.3)
        
        # 2. Simulate Live Sales
        print("\n" + "="*50)
        print("💰 SIMULATING LIVE SALES")
        print("="*50)
        
        sample_sales = [
            {'sale_id': 'S001', 'product_code': '001', 'amount': 150.50, 'region': 'North', 'type': 'Online'},
            {'sale_id': 'S002', 'product_code': '002', 'amount': 89.99, 'region': 'South', 'type': 'Retail'},
            {'sale_id': 'S003', 'product_code': '001', 'amount': 225.75, 'region': 'East', 'type': 'Wholesale'},
        ]
        
        for sale in sample_sales:
            self.kafka.send('clearvue-sales', sale)
            time.sleep(1)  # Simulate real-time interval
    
    def demonstrate_bi_pipeline(self):
        """Show the complete BI pipeline flow"""
        print("\n" + "="*50)
        print("🔄 DEMONSTRATING COMPLETE BI PIPELINE")
        print("="*50)
        
        # Stream data
        self.stream_all_data()
        
        # Consume and "process" data
        print("\n" + "="*50)
        print("📊 CONSUMING FOR BI DASHBOARD")
        print("="*50)
        
        # Simulate MongoDB storage
        print("💾 Storing in MongoDB...")
        products_in_db = self.kafka.consume('clearvue-products', limit=3)
        sales_in_db = self.kafka.consume('clearvue-sales', limit=2)
        
        # Simulate Power BI Dashboard
        print("\n" + "="*50)
        print("📈 POWER BI DASHBOARD UPDATES")
        print("="*50)
        print("✅ Real-time sales metrics updated")
        print("✅ Product performance charts refreshed") 
        print("✅ Regional sales heatmap live")
        print("✅ Inventory levels monitored")
        
        return {
            'products_processed': len(products_in_db),
            'sales_processed': len(sales_in_db),
            'total_messages': len(products_in_db) + len(sales_in_db)
        }

# Run the mock pipeline
if __name__ == "__main__":
    print("🎯 CLEARVUE BI - MOCK KAFKA PIPELINE")
    print("   (No installation required!)\n")
    
    pipeline = ClearVueMockPipeline()
    results = pipeline.demonstrate_bi_pipeline()
    
    print("\n" + "🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"   Processed: {results['total_messages']} total messages")
    print(f"   Products: {results['products_processed']} | Sales: {results['sales_processed']}")
    print("\n📋 This demonstrates your real Kafka pipeline will:")
    print("   - Stream product data in real-time")
    print("   - Process sales transactions") 
    print("   - Feed Power BI dashboards")
    print("   - Support real-time analytics")
    print("\n⚡ Use this while Docker installs!")