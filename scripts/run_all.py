"""python scripts/run_all.py --transactions 100000 --seed 42"""

import argparse

from fincrime_ai.pipeline import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    run(args.transactions, args.seed)
