from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np

app = FastAPI(title="Fraud Detection API")

# Load models
drift_model = joblib.load('models/drift_detector/model.pkl')
drift_scaler = joblib.load('models/drift_detector/scaler.pkl')
fraud_model = joblib.load('models/fraud_classifier/model.pkl')

DRIFT_FEATURES = ['TransactionAmt', 'dist1', 'dist2', 'C1', 'C2']
FRAUD_FEATURES = [
    'TransactionAmt', 'dist1', 'dist2',
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
    'C11', 'C12', 'C13', 'C14',
    'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
    'D1', 'D2', 'D3', 'D4'
]

class Transaction(BaseModel):
    transactions: list[dict]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/detect-drift")
def detect_drift(payload: Transaction):
    df = pd.DataFrame(payload.transactions)[DRIFT_FEATURES].fillna(0)
    X_scaled = drift_scaler.transform(df)
    scores = drift_model.decision_function(X_scaled)
    predictions = drift_model.predict(X_scaled)
    anomaly_count = int((predictions == -1).sum())
    healthy = float(scores.mean()) > -0.1

    return {
        "healthy": healthy,
        "anomaly_score": float(scores.mean()),
        "anomaly_count": anomaly_count,
        "total_records": len(payload.transactions)
    }

@app.post("/predict-fraud")
def predict_fraud(payload: Transaction):
    df = pd.DataFrame(payload.transactions)[FRAUD_FEATURES].fillna(0)
    predictions = fraud_model.predict(df)
    probabilities = fraud_model.predict_proba(df)[:, 1]

    return {
        "predictions": predictions.tolist(),
        "fraud_probabilities": probabilities.tolist(),
        "fraud_count": int(predictions.sum()),
        "total_records": len(payload.transactions)
    }

@app.post("/score")
def score(payload: Transaction):
    # First check drift
    drift_result = detect_drift(payload)
    
    if not drift_result["healthy"]:
        return {
            "status": "HALTED",
            "reason": "Data drift detected",
            "drift_score": drift_result["anomaly_score"],
            "anomaly_count": drift_result["anomaly_count"]
        }
    
    # If healthy run fraud detection
    fraud_result = predict_fraud(payload)
    
    return {
        "status": "OK",
        "drift_score": drift_result["anomaly_score"],
        "fraud_predictions": fraud_result["predictions"],
        "fraud_probabilities": fraud_result["fraud_probabilities"],
        "fraud_count": fraud_result["fraud_count"]
    }