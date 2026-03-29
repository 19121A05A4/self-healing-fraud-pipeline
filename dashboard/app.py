import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Self-Healing Fraud Pipeline",
    page_icon="🛡️",
    layout="wide"
)

API_URL = "http://40.65.88.4:8000"

# ── Header ────────────────────────────────────────────────────────────────
st.title("🛡️ Self-Healing Fraud Detection Pipeline")
st.markdown("Real-time fraud detection with automated data drift monitoring")

# ── API Health Check ──────────────────────────────────────────────────────
def check_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except:
        return False

health = check_health()
if health:
    st.success("✅ API Live — http://40.65.88.4:8000/docs")
else:
    st.error("❌ API Offline")

st.divider()

# ── Metrics Row ───────────────────────────────────────────────────────────
st.subheader("📊 Model Performance")
col1, col2, col3, col4 = st.columns(4)
col1.metric("ROC-AUC", "0.9656", "+0.37 vs baseline")
col2.metric("F1 Score", "0.59", "+0.42 vs baseline")
col3.metric("Recall", "0.83", "+0.05 vs baseline")
col4.metric("Features", "154", "+124 vs baseline")

st.divider()

# ── Live Transaction Scorer ───────────────────────────────────────────────
st.subheader("🔍 Live Transaction Scorer")
st.markdown("Submit a transaction to the live API and see fraud prediction + drift check in real time.")

PRESETS = {
    "🟢 Clean Transaction (Pipeline OK)": {
        "amt": 68.5, "d1": 14.0, "d2": 0.0, "c1": 1.0, "c2": 1.0, "drift": False,
        "desc": "A typical low-value transaction with normal feature values."
    },
    "🟡 Borderline Transaction (Pipeline OK)": {
        "amt": 4500.0, "d1": 315.0, "d2": 150.0, "c1": 5.0, "c2": 8.0, "drift": False,
        "desc": "Higher amount and distance — pipeline still processes but drift score is lower."
    },
    "🧪 Corrupt Data (Triggers Pipeline Halt)": {
        "amt": 0, "d1": 0, "d2": 0, "c1": 0, "c2": 0, "drift": True,
        "desc": "Simulates a data pipeline failure — extreme corrupt values trigger auto-halt."
    }
}

preset = st.selectbox("Select a demo scenario:", list(PRESETS.keys()))
selected = PRESETS[preset]

st.info(f"ℹ️ {selected['desc']}")

if not selected["drift"]:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Amount", f"${selected['amt']}")
    col2.metric("dist1", selected['d1'])
    col3.metric("dist2", selected['d2'])
    col4.metric("C1", selected['c1'])
    col5.metric("C2", selected['c2'])
else:
    st.warning("⚠️ Corrupt data mode: extreme values (999999999) will be sent to trigger pipeline halt")

if st.button("🚀 Score Transaction", type="primary"):
    if selected["drift"]:
        transaction = {
            "TransactionAmt": 999999999.0,
            "dist1": 999999999.0,
            "dist2": 999999999.0,
            "C1": 999999999.0,
            "C2": 999999999.0,
        }
    else:
        transaction = {
            "TransactionAmt": selected["amt"],
            "dist1": selected["d1"],
            "dist2": selected["d2"],
            "C1": selected["c1"],
            "C2": selected["c2"],
        }

    with st.spinner("Calling live Azure API..."):
        try:
            r = requests.post(
                f"{API_URL}/score",
                json={"transactions": [transaction]},
                timeout=10
            )
            result = r.json()

            st.divider()

            if result.get("status") == "HALTED":
                st.error("🚨 PIPELINE HALTED — Data Drift Detected")
                col1, col2 = st.columns(2)
                col1.metric("Drift Score", f"{result['drift_score']:.4f}")
                col2.metric("Anomalies Detected", result['anomaly_count'])
                st.warning("Pipeline automatically halted. Engineer alert triggered.")
            else:
                st.success("✅ Pipeline OK — Transaction Scored")
                col1, col2, col3 = st.columns(3)
                col1.metric("Status", "OK")
                col2.metric("Drift Score", f"{result['drift_score']:.4f}")
                col3.metric("Fraud Count", result['fraud_count'])

                fraud_prob = result['fraud_probabilities'][0]
                prediction = result['fraud_predictions'][0]

                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Fraud Prediction",
                        "🚨 FRAUD" if prediction == 1 else "✅ LEGITIMATE"
                    )
                with col2:
                    st.metric("Fraud Probability", f"{fraud_prob:.4f}")

                st.progress(float(fraud_prob), text=f"Fraud Risk: {fraud_prob*100:.1f}%")

        except Exception as e:
            st.error(f"API Error: {e}")

st.divider()

# ── Architecture ──────────────────────────────────────────────────────────
st.subheader("🏗️ System Architecture")
st.code("""
Transaction Stream (Kafka)
        ↓
Feature Extractor (Spark)
        ↓
┌─────────────────────────┐
│  Layer 1: Isolation     │  ← monitors feature distribution
│  Forest (Drift Check)   │
└────────────┬────────────┘
        ↓              ↓
   Data OK         Data Drifted
        ↓              ↓
Fraud Classifier   HALT + ALERT
(XGBoost)
        ↓
  Airflow → dbt → Snowflake
""")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────
st.subheader("📈 Model Evaluation")
col1, col2 = st.columns(2)
with col1:
    st.image("docs/confusion_matrix.png", caption="Confusion Matrix", use_column_width=True)
with col2:
    st.image("docs/roc_curve.png", caption="ROC Curve — AUC 0.9656", use_column_width=True)

st.divider()

# ── What Makes It Different ───────────────────────────────────────────────
st.subheader("⚡ What Makes This Different")
col1, col2 = st.columns(2)
with col1:
    st.error("❌ Traditional Fraud Pipeline")
    st.markdown("""
    - Detects fraud only
    - Fails silently on bad data
    - Engineer finds out hours later
    - No self-awareness
    """)
with col2:
    st.success("✅ This System")
    st.markdown("""
    - Detects fraud + monitors data health
    - Halts automatically on drift
    - Engineer alerted immediately
    - MLOps-aware architecture
    """)

st.divider()
st.caption("Built by Sai Katari | University of Kansas MS CS 2026 | Live API: http://40.65.88.4:8000/docs")