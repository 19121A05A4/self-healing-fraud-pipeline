import json
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'raw-transactions',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest'
)

print("Listening for transactions...")

for i, message in enumerate(consumer):
    transaction = message.value
    print(f"Transaction {i}: ID={transaction.get('TransactionID')} Amount={transaction.get('TransactionAmt')}")
    
    if i >= 10:  # print first 10 then stop
        break