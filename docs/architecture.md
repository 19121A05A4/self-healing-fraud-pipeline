# System Architecture

## Self-Healing Fraud Detection Pipeline
```
IEEE-CIS Dataset (590K transactions)
            │
            ▼
    ┌───────────────┐
    │ Kafka Producer │  ← Simulates real-time transaction stream
    └───────┬───────┘
            │ raw-transactions topic
            ▼
    ┌───────────────────────────────────┐
    │         Pipeline Runner           │
    │                                   │
    │  ┌─────────────────────────────┐  │
    │  │  Layer 1: Isolation Forest  │  │
    │  │  "Is this data healthy?"    │  │
    │  └──────────┬──────────────────┘  │
    │             │                     │
    │        ┌────┴─────┐               │
    │      Healthy    Drifted           │
    │        │           │              │
    │        ▼           ▼              │
    │  ┌──────────┐  ┌────────────┐    │
    │  │ XGBoost  │  │   HALT +   │    │
    │  │ Fraud    │  │   ALERT    │    │
    │  │Classifier│  └────────────┘    │
    │  └────┬─────┘                    │
    └───────┼──────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │    AWS S3     │  ← Raw + scored data lake
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │Apache Airflow │  ← Hourly DAG orchestration
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │      dbt      │  ← staging → intermediate → marts
    └───────┬───────┘
            │
            ▼
    ┌───────────────┐
    │   Snowflake   │  ← Analytics-ready warehouse
    └───────────────┘
```

## Components

| Component | Tool | Purpose |
|---|---|---|
| Streaming | Apache Kafka | Real-time transaction ingestion |
| Drift Detection | Isolation Forest | Monitor incoming data health |
| Fraud Classification | XGBoost | Binary fraud prediction |
| Model Serving | FastAPI | REST endpoints for both models |
| Orchestration | Apache Airflow | Pipeline scheduling and DAGs |
| Transformation | dbt | SQL transformation layers |
| Warehouse | Snowflake | Analytics-ready storage |
| Infrastructure | Docker | Containerized deployment |