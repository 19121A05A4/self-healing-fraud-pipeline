import pandas as pd
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaProducer, KafkaConsumer
from models.drift_detector.predict import is_data_healthy
from models.fraud_classifier.predict import predict_fraud
from alerts.notifier import send_drift_alert

BATCH_SIZE = 100
KAFKA_TOPIC = 'raw-transactions'
BOOTSTRAP_SERVERS = 'localhost:9092'

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='latest',
    group_id='fraud-pipeline'
)

def process_batch(batch):
    print(f"\n--- Processing batch of {len(batch)} transactions ---")

    # Step 1: Check data health
    drift_result = is_data_healthy(batch)
    print(f"Drift check: score={drift_result['anomaly_score']:.4f}, healthy={drift_result['healthy']}")

    if not drift_result['healthy']:
        print("🚨 DATA DRIFT DETECTED - Halting pipeline!")
        send_drift_alert(
            anomaly_score=drift_result['anomaly_score'],
            anomaly_count=drift_result['anomaly_count'],
            total_records=drift_result['total_records']
        )
        return {"status": "HALTED", "reason": "drift_detected"}

    # Step 2: Run fraud detection
    fraud_result = predict_fraud(batch)
    print(f"Fraud check: {fraud_result['fraud_count']} fraudulent transactions detected")

    return {
        "status": "OK",
        "batch_size": len(batch),
        "fraud_count": fraud_result['fraud_count'],
        "drift_score": drift_result['anomaly_score']
    }

print("Starting pipeline... listening for transactions")
batch = []

for message in consumer:
    transaction = message.value
    batch.append(transaction)

    if len(batch) >= BATCH_SIZE:
        result = process_batch(batch)
        print(f"Result: {result}")
        batch = []

        if result['status'] == 'HALTED':
            print("Pipeline halted due to drift. Restart after investigating.")
            break