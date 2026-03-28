from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import pandas as pd
import snowflake.connector
import os

default_args = {
    'owner': 'sai',
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def load_transactions_to_snowflake():
    df = pd.read_csv('data/train_transaction.csv')
    
    # Take sample for pipeline demo
    df_sample = df.sample(n=10000, random_state=42).fillna(0)
    
    conn = snowflake.connector.connect(
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        warehouse='FRAUD_WH',
        database='FRAUD_PIPELINE',
        schema='RAW'
    )
    
    cursor = conn.cursor()
    
    # Create raw table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RAW_TRANSACTIONS (
            TRANSACTIONID NUMBER,
            TRANSACTIONAMT FLOAT,
            PRODUCTCD VARCHAR,
            DIST1 FLOAT,
            DIST2 FLOAT,
            C1 FLOAT, C2 FLOAT, C3 FLOAT, C4 FLOAT,
            ISFRAUD NUMBER
        )
    """)
    
    # Insert rows
    insert_sql = """
        INSERT INTO RAW_TRANSACTIONS 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    rows = df_sample[[
        'TransactionID', 'TransactionAmt', 'ProductCD',
        'dist1', 'dist2', 'C1', 'C2', 'C3', 'C4', 'isFraud'
    ]].values.tolist()
    
    cursor.executemany(insert_sql, rows)
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Loaded {len(rows)} transactions to Snowflake RAW schema")

def check_data_quality():
    conn = snowflake.connector.connect(
        user=os.environ['SNOWFLAKE_USER'],
        password=os.environ['SNOWFLAKE_PASSWORD'],
        account=os.environ['SNOWFLAKE_ACCOUNT'],
        warehouse='FRAUD_WH',
        database='FRAUD_PIPELINE',
        schema='RAW'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM RAW_TRANSACTIONS")
    count = cursor.fetchone()[0]
    print(f"Row count check: {count} rows in RAW_TRANSACTIONS")
    assert count > 0, "No data found in RAW_TRANSACTIONS"
    cursor.close()
    conn.close()

with DAG(
    dag_id='fraud_pipeline_dag',
    default_args=default_args,
    description='Load and transform fraud transaction data',
    schedule='@hourly',
    start_date=datetime(2026, 1, 1),
    catchup=False
) as dag:

    load_task = PythonOperator(
        task_id='load_transactions_to_snowflake',
        python_callable=load_transactions_to_snowflake
    )

    quality_task = PythonOperator(
        task_id='check_data_quality',
        python_callable=check_data_quality
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd dbt && dbt run --profiles-dir .'
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd dbt && dbt test --profiles-dir .'
    )

    load_task >> quality_task >> dbt_run >> dbt_test