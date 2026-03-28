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
# Send ONLY corrupted records in rapid succession
for idx, row in df.iloc[500:600].iterrows():
    corrupted = row.to_dict()
    corrupted['TransactionAmt'] = 999999999  # extreme value
    corrupted['C1'] = 999999999
    corrupted['C2'] = 999999999
    corrupted['dist1'] = 999999999
    corrupted['dist2'] = 999999999
    producer.send('raw-transactions', value=corrupted)

# Fill entire batch with corrupted data
for i in range(400):  # send 400 more corrupted records
    corrupted = df.iloc[0].to_dict()
    corrupted['TransactionAmt'] = 999999999
    corrupted['C1'] = 999999999
    corrupted['dist1'] = 999999999
    producer.send('raw-transactions', value=corrupted)

print("Drift injection complete.")
producer.flush()