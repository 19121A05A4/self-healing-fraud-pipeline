import pandas as pd
import json
import time
from kafka import KafkaProducer

df = pd.read_csv('data/train_transaction.csv')

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Streaming normal transactions for 30 seconds...")
for idx, row in df.iloc[:500].iterrows():
    producer.send('raw-transactions', value=row.to_dict())
    time.sleep(0.05)

print("INJECTING DRIFT NOW...")
# Corrupt the data — simulate drift
for idx, row in df.iloc[500:600].iterrows():
    corrupted = row.to_dict()
    corrupted['TransactionAmt'] = corrupted['TransactionAmt'] * 1000  # extreme values
    corrupted['C1'] = None  # nulls
    corrupted['dist1'] = -999  # impossible values
    producer.send('raw-transactions', value=corrupted)
    time.sleep(0.05)

print("Drift injection complete.")
producer.flush()