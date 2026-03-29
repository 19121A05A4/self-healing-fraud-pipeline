from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np

app = FastAPI(title="Fraud Detection API")

# Load models
drift_model = joblib.load('model.pkl')
drift_scaler = joblib.load('scaler.pkl')
fraud_model = joblib.load('fraud_model.pkl')

DRIFT_FEATURES = ['TransactionAmt', 'dist1', 'dist2', 'C1', 'C2']
FRAUD_FEATURES = [
    'TransactionAmt', 'TransactionAmt_log', 'hour', 'day',
    'ProductCD', 'card1', 'card2', 'card3', 'card4', 'card5', 'card6',
    'addr1', 'addr2', 'dist1', 'dist2',
    'P_emaildomain', 'R_emaildomain',
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
    'C11', 'C12', 'C13', 'C14',
    'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10',
    'D11', 'D12', 'D13', 'D14', 'D15',
    'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9',
    'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
    'V11', 'V12', 'V13', 'V14', 'V15', 'V16', 'V17', 'V18', 'V19', 'V20',
    'V21', 'V22', 'V23', 'V24', 'V25', 'V26', 'V27', 'V28', 'V29', 'V30',
    'V31', 'V32', 'V33', 'V34', 'V35', 'V36', 'V37', 'V38', 'V39', 'V40',
    'V41', 'V42', 'V43', 'V44', 'V45', 'V46', 'V47', 'V48', 'V49', 'V50',
    'V51', 'V52', 'V53', 'V54', 'V55', 'V56', 'V57', 'V58', 'V59', 'V60',
    'V61', 'V62', 'V63', 'V64', 'V65', 'V66', 'V67', 'V68', 'V69', 'V70',
    'V71', 'V72', 'V73', 'V74', 'V75', 'V76', 'V77', 'V78', 'V79', 'V80',
    'V81', 'V82', 'V83', 'V84', 'V85', 'V86', 'V87', 'V88', 'V89', 'V90',
    'V91', 'V92', 'V93', 'V94', 'V95', 'V96', 'V97', 'V98', 'V99'
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
    df = pd.DataFrame(payload.transactions).fillna(0)
    
    # Engineer features to match training
    df['TransactionAmt_log'] = np.log1p(df['TransactionAmt'])
    df['hour'] = 0
    df['day'] = 0
    
    # Add missing columns with 0
    for col in FRAUD_FEATURES:
        if col not in df.columns:
            df[col] = 0
    
    df = df[FRAUD_FEATURES].fillna(0)
    probabilities = fraud_model.predict_proba(df)[:, 1]
    predictions = (probabilities >= 0.7813).astype(int)

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