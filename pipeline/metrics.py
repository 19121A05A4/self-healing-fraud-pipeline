import json
from datetime import datetime

metrics = {
    "project": "Self-Healing Fraud Detection Pipeline",
    "date": str(datetime.now().date()),
    "dataset": {
        "name": "IEEE-CIS Fraud Detection",
        "total_transactions": 590540,
        "fraud_rate_pct": 3.50,
        "features_used": 30
    },
    "fraud_classifier": {
        "model": "XGBoost",
        "precision": 0.21,
        "recall": 0.78,
        "f1_score": 0.33,
        "accuracy": 0.89,
        "note": "High recall prioritized — missing fraud is more costly than false positives"
    },
    "drift_detector": {
        "model": "Isolation Forest",
        "contamination": 0.01,
        "n_estimators": 100,
        "drift_detection_score_normal": 0.34,
        "drift_detection_score_drifted": -0.18,
        "anomalies_detected_on_drift": "100/100 records"
    },
    "pipeline_performance": {
        "batch_size": 100,
        "batches_processed_before_drift": 8,
        "drift_detected": True,
        "pipeline_halted_automatically": True,
        "alert_triggered": True
    },
    "stack": [
        "Apache Kafka",
        "XGBoost",
        "Isolation Forest",
        "FastAPI",
        "Apache Airflow",
        "dbt",
        "Snowflake",
        "Docker"
    ]
}

with open('docs/metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print("Metrics saved to docs/metrics.json")
print(json.dumps(metrics, indent=2))