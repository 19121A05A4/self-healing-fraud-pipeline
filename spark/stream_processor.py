from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import *
import requests
import json

# Define schema for incoming transactions
schema = StructType([
    StructField("TransactionID", LongType()),
    StructField("TransactionAmt", DoubleType()),
    StructField("ProductCD", StringType()),
    StructField("card4", StringType()),
    StructField("card6", StringType()),
    StructField("P_emaildomain", StringType()),
    StructField("dist1", DoubleType()),
    StructField("dist2", DoubleType()),
    StructField("C1", DoubleType()),
    StructField("C2", DoubleType()),
    StructField("isFraud", IntegerType())
])

spark = SparkSession.builder \
    .appName("FraudPipelineProcessor") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "raw-transactions") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON
parsed = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# Select numeric features only
features = parsed.select(
    "TransactionID",
    "TransactionAmt",
    "dist1",
    "dist2",
    "C1",
    "C2"
).fillna(0)

def process_batch(batch_df, batch_id):
    if batch_df.count() == 0:
        return
    
    rows = batch_df.toPandas()
    print(f"\nBatch {batch_id}: {len(rows)} transactions received")
    print(rows[["TransactionID", "TransactionAmt"]].head(5))
    
    # Week 3: drift detection + fraud scoring will plug in here

query = features.writeStream \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", "/tmp/checkpoint") \
    .start()

query.awaitTermination()