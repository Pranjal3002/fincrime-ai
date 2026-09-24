"""Central paths and versioned, reviewable controls."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("FINCRIME_DATA_DIR", ROOT / "data"))
REPORTS = ROOT / "reports"
ARTIFACTS = ROOT / "artifacts"


def controls():
    return json.loads((ROOT / "config/rules.json").read_text())


def prepare():
    for path in [REPORTS, ARTIFACTS] + [
        DATA / name for name in ["raw", "processed", "curated", "reference"]
    ]:
        path.mkdir(parents=True, exist_ok=True)
