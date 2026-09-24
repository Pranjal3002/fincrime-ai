"""Capture real test/check output with machine-specific path redaction."""

import json
import subprocess
import sys

import httpx

from fincrime_ai.settings import REPORTS, ROOT


def main():
    results = {}
    commands = {
        "pytest": [sys.executable, "-m", "pytest", "-q"],
        "ruff": [sys.executable, "-m", "ruff", "check", "."],
        "black": [sys.executable, "-m", "black", "--check", "."],
    }
    for name, command in commands.items():
        result = subprocess.run(
            command,
            check=False,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = (
            (result.stdout + result.stderr)
            .replace(str(ROOT), "<repository>")
            .replace(str(ROOT).lower(), "<repository>")
        )
        (REPORTS / f"{name}_output.txt").write_text(output, encoding="utf-8")
        results[name] = {
            "command": "python -m " + " ".join(command[2:]),
            "exit_code": result.returncode,
            "output": output,
        }
        print(f"{name}: exit {result.returncode}", flush=True)
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
        responses = {
            route: client.get(route).status_code
            for route in [
                "/health",
                "/alerts?limit=2",
                "/analytics/summary",
                "/model/metrics",
                "/openapi.json",
            ]
        }
        responses["POST /score/transaction"] = client.post(
            "/score/transaction", json={"transaction_id": "SYN-TX-0000001"}
        ).status_code
        responses["POST /screen/entity"] = client.post(
            "/screen/entity",
            json={"name": "Fictional Zorvex Amber Trading", "country": "GB"},
        ).status_code
        alert = client.get("/alerts?limit=1").json()[0]["alert_id"]
        responses["POST /investigation/summary"] = client.post(
            f"/investigation/{alert}/summary"
        ).status_code
    results["api_smoke"] = responses
    results["streamlit_health"] = httpx.get(
        "http://127.0.0.1:8501/_stcore/health"
    ).status_code
    results["python_version"] = sys.version.split()[0]
    (REPORTS / "validation_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    if (
        any(results[n]["exit_code"] for n in commands)
        or any(code != 200 for code in responses.values())
        or results["streamlit_health"] != 200
    ):
        raise SystemExit(1)
    print("All checks and live service smoke tests passed")


if __name__ == "__main__":
    main()
