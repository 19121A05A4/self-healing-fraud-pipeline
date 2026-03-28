import numpy as np
import joblib
import pandas as pd

model = joblib.load('models/drift_detector/model.pkl')
scaler = joblib.load('models/drift_detector/scaler.pkl')

FEATURE_COLS = ['TransactionAmt', 'dist1', 'dist2', 'C1', 'C2']
THRESHOLD = -0.1  # tune this based on your validation

def is_data_healthy(transactions: list[dict]) -> dict:
    """
    Input: list of transaction dicts
    Output: {healthy: bool, anomaly_score: float, anomaly_count: int}
    """
    df = pd.DataFrame(transactions)[FEATURE_COLS].fillna(0)
    X_scaled = scaler.transform(df)
    
    scores = model.decision_function(X_scaled)
    predictions = model.predict(X_scaled)  # 1=normal, -1=anomaly
    
    anomaly_count = (predictions == -1).sum()
    avg_score = scores.mean()
    healthy = avg_score > THRESHOLD
    
    return {
        "healthy": bool(healthy),
        "anomaly_score": float(avg_score),
        "anomaly_count": int(anomaly_count),
        "total_records": len(transactions)
    }