import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Load dataset
df = pd.read_csv('data/train_transaction.csv')

# Select numeric features used in pipeline
feature_cols = ['TransactionAmt', 'dist1', 'dist2', 'C1', 'C2']
X = df[feature_cols].fillna(0)

# Train only on clean data (first 100K rows as baseline)
X_train = X.iloc[:100000]

print(f"Training Isolation Forest on {len(X_train)} clean transactions...")

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)

# Train Isolation Forest
model = IsolationForest(
    n_estimators=100,
    contamination=0.01,  # expect 1% anomalies
    random_state=42
)
model.fit(X_scaled)

# Save model and scaler
os.makedirs('models/drift_detector', exist_ok=True)
joblib.dump(model, 'models/drift_detector/model.pkl')
joblib.dump(scaler, 'models/drift_detector/scaler.pkl')

print("Isolation Forest trained and saved.")

# Quick validation
scores = model.decision_function(X_scaled[:1000])
print(f"Anomaly score range: {scores.min():.3f} to {scores.max():.3f}")
print(f"Anomalies detected in first 1000: {(model.predict(X_scaled[:1000]) == -1).sum()}")