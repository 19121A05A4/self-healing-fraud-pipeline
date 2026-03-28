import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
import joblib
import os

# Load dataset
df = pd.read_csv('data/train_transaction.csv')

# Features and label
feature_cols = [
    'TransactionAmt', 'dist1', 'dist2',
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10',
    'C11', 'C12', 'C13', 'C14',
    'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10',
    'D1', 'D2', 'D3', 'D4'
]
X = df[feature_cols].fillna(0)
y = df['isFraud']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training on {len(X_train)} transactions...")
print(f"Fraud rate: {y_train.mean()*100:.2f}%")

# Train XGBoost
model = XGBClassifier(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05,
    scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='logloss'
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print(f"F1 Score: {f1_score(y_test, y_pred):.4f}")

# Save model
os.makedirs('models/fraud_classifier', exist_ok=True)
joblib.dump(model, 'models/fraud_classifier/model.pkl')
print("XGBoost model saved.")