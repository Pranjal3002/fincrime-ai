"""Execute Spark and reconcile its actual output against the synthetic source."""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from fincrime_ai.settings import DATA, REPORTS
from fincrime_ai.spark_pipeline import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--existing-result",
        help="Validate output from a completed Spark run using its recorded JSON stdout",
    )
    args = parser.parse_args()
    os.environ["PYSPARK_PYTHON"] = sys.executable
    if args.existing_result:
        content = Path(args.existing_result).read_bytes()
        text = content.decode("utf-16" if content.startswith(b"\xff\xfe") else "utf-8")
        result = json.loads(
            next(line for line in text.splitlines() if line.startswith('{"engine"'))
        )
    else:
        result = run(
            DATA / "raw/transactions.parquet",
            DATA / "processed/spark_transactions.parquet",
            "arrow",
        )
    raw = (
        pd.read_parquet(DATA / "raw/transactions.parquet")
        .set_index("transaction_id")
        .sort_index()
    )
    actual = (
        pd.read_parquet(DATA / "processed/spark_transactions.parquet")
        .set_index("transaction_id")
        .sort_index()
    )
    assert raw.index.equals(actual.index)
    assert actual.index.is_unique and len(raw) == len(actual)
    np.testing.assert_allclose(actual.amount, raw.amount, rtol=0, atol=0)
    np.testing.assert_allclose(actual.amount_log, np.log1p(raw.amount), rtol=1e-12)
    assert (pd.to_datetime(actual.payment_date).dt.date == raw.timestamp.dt.date).all()
    result.update(
        {
            "pyspark_version": "3.5.5",
            "local_master": "local[2]",
            "id_parity": True,
            "row_count_parity": True,
            "amount_parity": True,
            "log_amount_parity": True,
            "date_parity": True,
            "native_hadoop_export": "Attempted and failed: Windows winutils/HADOOP_HOME unavailable. Arrow writer used for local export; transformations executed in Spark.",
        }
    )
    (REPORTS / "spark_validation.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result))
