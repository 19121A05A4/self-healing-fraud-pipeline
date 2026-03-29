import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, f1_score, 
                             roc_auc_score, confusion_matrix, 
                             roc_curve, precision_recall_curve)
import matplotlib.pyplot as plt
import joblib
import os

# ── Load and merge both tables ──────────────────────────────────────────
print("Loading data...")
trans = pd.read_csv('data/train_transaction.csv')
identity = pd.read_csv('data/train_identity.csv')
df = trans.merge(identity, on='TransactionID', how='left')
print(f"Dataset shape after merge: {df.shape}")

# ── Feature Engineering ──────────────────────────────────────────────────
print("Engineering features...")

# Log transform transaction amount (heavy right skew)
df['TransactionAmt_log'] = np.log1p(df['TransactionAmt'])

# Time features
df['hour'] = (df['TransactionDT'] / 3600 % 24).astype(int)
df['day'] = (df['TransactionDT'] / (3600 * 24) % 7).astype(int)

# Encode categorical columns
cat_cols = ['ProductCD', 'card4', 'card6', 'P_emaildomain', 
            'R_emaildomain', 'M1', 'M2', 'M3', 'M4', 'M5', 
            'M6', 'M7', 'M8', 'M9']
for col in cat_cols:
    if col in df.columns:
        df[col] = pd.Categorical(df[col]).codes

# ── Select Features ──────────────────────────────────────────────────────
# Core numeric features
base_features = [
    'TransactionAmt', 'TransactionAmt_log', 'hour', 'day',
    'ProductCD', 'card1', 'card2', 'card3', 'card4', 'card5', 'card6',
    'addr1', 'addr2', 'dist1', 'dist2',
    'P_emaildomain', 'R_emaildomain'
]

# C features (count features)
c_features = [f'C{i}' for i in range(1, 15)]

# D features (time delta features)
d_features = [f'D{i}' for i in range(1, 16)]

# M features (match features)
m_features = [f'M{i}' for i in range(1, 10)]

# V features (Vesta engineered — top ones by variance)
v_features = [f'V{i}' for i in range(1, 100)]

all_features = base_features + c_features + d_features + m_features + v_features

# Keep only columns that exist
feature_cols = [f for f in all_features if f in df.columns]
print(f"Using {len(feature_cols)} features")

X = df[feature_cols].fillna(-999)
y = df['isFraud']

# ── Train/Test Split ─────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training on {len(X_train)} transactions...")
print(f"Fraud rate: {y_train.mean()*100:.2f}%")

# ── Train XGBoost ────────────────────────────────────────────────────────
scale_pos = (y_train == 0).sum() / (y_train == 1).sum()

model = XGBClassifier(
    n_estimators=500,
    max_depth=9,
    learning_rate=0.05,
    scale_pos_weight=scale_pos,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    gamma=1,
    random_state=42,
    eval_metric='auc',
    early_stopping_rounds=50,
    verbosity=1
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=50
)

# ── Evaluate ─────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("\n" + "="*50)
print("CLASSIFICATION REPORT")
print("="*50)
print(classification_report(y_test, y_pred))
print(f"F1 Score:  {f1_score(y_test, y_pred):.4f}")
print(f"ROC-AUC:   {roc_auc_score(y_test, y_prob):.4f}")

# ── Confusion Matrix ──────────────────────────────────────────────────────
os.makedirs('docs', exist_ok=True)
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm, cmap='Blues')
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(['Not Fraud', 'Fraud'])
ax.set_yticklabels(['Not Fraud', 'Fraud'])
ax.set_xlabel('Predicted')
ax.set_ylabel('Actual')
ax.set_title('Confusion Matrix')
for i in range(2):
    for j in range(2):
        ax.text(j, i, str(cm[i][j]), ha='center', va='center',
                color='white' if cm[i][j] > cm.max()/2 else 'black',
                fontsize=14, fontweight='bold')
plt.colorbar(im)
plt.tight_layout()
plt.savefig('docs/confusion_matrix.png', dpi=150)
print("Saved: docs/confusion_matrix.png")

# ── ROC Curve ─────────────────────────────────────────────────────────────
fpr, tpr, _ = roc_curve(y_test, y_prob)
auc = roc_auc_score(y_test, y_prob)
fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(fpr, tpr, color='#1976D2', lw=2, label=f'ROC Curve (AUC = {auc:.4f})')
ax.plot([0, 1], [0, 1], color='gray', linestyle='--', lw=1)
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curve — Fraud Classifier')
ax.legend(loc='lower right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('docs/roc_curve.png', dpi=150)
print("Saved: docs/roc_curve.png")

# ── Precision-Recall Curve ────────────────────────────────────────────────
precision, recall, _ = precision_recall_curve(y_test, y_prob)
fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(recall, precision, color='#E53935', lw=2)
ax.set_xlabel('Recall')
ax.set_ylabel('Precision')
ax.set_title('Precision-Recall Curve — Fraud Classifier')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('docs/precision_recall_curve.png', dpi=150)
print("Saved: docs/precision_recall_curve.png")

# ── Save Model ────────────────────────────────────────────────────────────
joblib.dump(model, 'models/fraud_classifier/model.pkl')
print(f"\nModel saved. Features used: {len(feature_cols)}")
print(f"Final ROC-AUC: {auc:.4f}")