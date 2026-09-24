"""Optional dedicated local Spark transformation. Run with Spark extra installed."""

import argparse
import json
import os
import time
from pathlib import Path


def run(source, target, writer="auto"):
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as f

    started = time.perf_counter()
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("FinCrimeAI-local")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    try:
        frame = spark.read.parquet(str(source))
        transformed = (
            frame.withColumn("payment_date", f.to_date("timestamp"))
            .withColumn("amount_log", f.log1p("amount"))
            .filter(f.col("amount") > 0)
            .dropDuplicates(["transaction_id"])
        )
        count = transformed.count()
        writer = (
            "arrow"
            if writer == "auto" and os.name == "nt"
            else "spark" if writer == "auto" else writer
        )
        if writer == "arrow":
            # Windows Hadoop-native file writes require winutils. Spark still performs
            # every transformation; only the bounded local export uses PyArrow.
            import pyarrow as pa
            import pyarrow.parquet as pq

            target = Path(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            buffer = []
            parquet_writer = None
            try:
                for row in transformed.toLocalIterator():
                    buffer.append(row.asDict())
                    if len(buffer) == 10000:
                        table = pa.Table.from_pylist(buffer)
                        if parquet_writer is None:
                            parquet_writer = pq.ParquetWriter(target, table.schema)
                        parquet_writer.write_table(table)
                        buffer.clear()
                if buffer:
                    table = pa.Table.from_pylist(buffer)
                    if parquet_writer is None:
                        parquet_writer = pq.ParquetWriter(target, table.schema)
                    parquet_writer.write_table(table)
            finally:
                if parquet_writer is not None:
                    parquet_writer.close()
        else:
            transformed.write.mode("overwrite").parquet(str(target))
        return {
            "engine": "pyspark",
            "writer": writer,
            "rows": count,
            "seconds": time.perf_counter() - started,
        }
    finally:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/raw/transactions.parquet")
    parser.add_argument("--target", default="data/processed/spark_transactions.parquet")
    parser.add_argument("--writer", choices=["auto", "arrow", "spark"], default="auto")
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.target, args.writer)))
