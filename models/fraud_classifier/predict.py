import joblib
import pandas as pd

model = joblib.load('models/fraud_classifier/model.pkl')

FRAUD_FEATURES = [
    'TransactionAmt', 'dist1', 'dist2',
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
    'C11', 'C12', 'C13', 'C14',
    'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
    'D1', 'D2', 'D3', 'D4'
]

def predict_fraud(transactions: list[dict]) -> dict:
    df = pd.DataFrame(transactions)[FRAUD_FEATURES].fillna(0)
    predictions = model.predict(df)
    probabilities = model.predict_proba(df)[:, 1]

    return {
        "predictions": predictions.tolist(),
        "fraud_probabilities": probabilities.tolist(),
        "fraud_count": int(predictions.sum()),
        "total_records": len(transactions)
    }