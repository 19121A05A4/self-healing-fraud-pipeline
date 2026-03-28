import pandas as pd
import json
import time
from kafka import KafkaProducer

# Load dataset
df = pd.read_csv('data/train_transaction.csv')

# Initialize producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print(f"Streaming {len(df)} transactions to Kafka...")

for idx, row in df.iterrows():
    transaction = row.to_dict()
    producer.send('raw-transactions', value=transaction)
    
    if idx % 100 == 0:
        print(f"Sent {idx} transactions")
    
    time.sleep(0.01)  # simulate real-time stream

producer.flush()
print("Done streaming.")