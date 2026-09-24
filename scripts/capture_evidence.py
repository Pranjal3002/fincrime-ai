"""Capture actual local app renders; never generate synthetic success screenshots."""

import hashlib
import html
import json
import re

import duckdb
from playwright.sync_api import expect, sync_playwright

from fincrime_ai.settings import DATA, REPORTS, ROOT


def main():
    images = ROOT / "docs/images"
    manifest = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1500, "height": 1080}, device_scale_factor=1
        )
        page.goto("http://127.0.0.1:8501", wait_until="domcontentloaded")
        pages = [
            ("Executive Overview", "01_executive_dashboard.png"),
            ("Screening Analytics", "02_screening_dashboard.png"),
            ("Payment Risk", "03_geographic_risk.png"),
            ("Model Performance", "04_model_performance.png"),
            ("Statistical Analysis", "07_statistical_analysis.png"),
            ("Investigation Explorer", "08_alert_investigation.png"),
        ]
        for title, filename in pages:
            page.locator("label").filter(
                has=page.get_by_role("radio", name=title, exact=True)
            ).click()
            expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible(
                timeout=60000
            )
            expect(page.locator('[data-testid="stException"]')).to_have_count(0)
            # Wait for the app's final caption and browser fonts; charts render client-side.
            expect(
                page.get_by_text(
                    "This is an educational portfolio simulation and is not intended for production compliance, AML, sanctions, or financial-crime decisioning.",
                    exact=True,
                )
            ).to_be_visible(timeout=60000)
            page.evaluate("document.fonts.ready")
            expect(
                page.get_by_role("button", name="Stop", exact=True)
            ).not_to_be_visible(timeout=60000)
            expect(page.locator('[data-stale="true"]')).to_have_count(0, timeout=60000)
            if title != "Investigation Explorer":
                expect(
                    page.locator('[data-testid="stPlotlyChart"]').first
                ).to_be_visible(timeout=60000)
            page.screenshot(
                path=str(images / filename), full_page=True, animations="disabled"
            )
            manifest.append(
                {
                    "file": filename,
                    "source": f"Streamlit / {title}",
                    "kind": "actual browser screenshot",
                }
            )
        # Exercise filter behavior without altering case state.
        page.locator("label").filter(
            has=page.get_by_role("radio", name="Executive Overview", exact=True)
        ).click()
        expect(
            page.get_by_role("heading", name="Executive Overview", exact=True)
        ).to_be_visible()
        page.get_by_role("button", name="Remove API", exact=True).click()
        stats = json.loads((REPORTS / "statistics.json").read_text())
        records = json.loads((REPORTS / "run_manifest.json").read_text())["records"]
        expected_count = records - stats["channel_counts"]["API"]
        expect(page.locator('[data-testid="stMetricValue"]').first).to_have_text(
            f"{expected_count:,}", timeout=30000
        )
        page.get_by_role("button", name="Clear all", exact=True).click()
        expect(
            page.get_by_text("Select at least one channel.", exact=True)
        ).to_be_visible(timeout=30000)
        (REPORTS / "ui_smoke.json").write_text(
            json.dumps(
                {
                    "pages_rendered": [title for title, _ in pages],
                    "remove_api_expected_count": expected_count,
                    "remove_api_filter_passed": True,
                    "empty_filter_state_passed": True,
                    "case_state_mutated": False,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        page.goto("http://127.0.0.1:8000/docs", wait_until="networkidle")
        expect(
            page.get_by_role("heading", name=re.compile("FinCrimeAI"))
        ).to_be_visible(timeout=30000)
        expect(page.get_by_text("/score/transaction", exact=True).first).to_be_visible(
            timeout=30000
        )
        page.screenshot(path=str(images / "09_fastapi_docs.png"), full_page=True)
        manifest.append(
            {
                "file": "09_fastapi_docs.png",
                "source": "FastAPI live /docs",
                "kind": "actual browser screenshot",
            }
        )
        # Terminal-style evidence explicitly reproduces captured real output, not a terminal photo.
        for source, filename, title in [
            (
                "pytest_output.txt",
                "10_tests_passed.png",
                "Actual pytest command output",
            ),
            (
                "pipeline_output.txt",
                "11_pipeline_run.png",
                "Actual pipeline command output",
            ),
        ]:
            text = (REPORTS / source).read_text(encoding="utf-8")
            page.set_content(
                f"<html><body style='background:#11283e;color:#e7f0f8;font-family:Consolas,monospace;padding:42px'><h1>{title}</h1><p>FinCrimeAI • rendered transcript of actual execution</p><pre style='font-size:19px;white-space:pre-wrap'>{html.escape(text)}</pre></body></html>"
            )
            page.screenshot(path=str(images / filename), full_page=True)
            manifest.append(
                {
                    "file": filename,
                    "source": f"reports/{source}",
                    "kind": "rendered actual command transcript",
                }
            )
        with duckdb.connect(str(DATA / "warehouse.duckdb"), read_only=True) as conn:
            constraints = conn.execute(
                "SELECT table_name,constraint_type,constraint_text FROM duckdb_constraints() ORDER BY table_name,constraint_type"
            ).df()
            tables = conn.execute("SHOW TABLES").df()
        page.set_content(
            "<html><body style='background:#f4f7fb;color:#102a43;font-family:Segoe UI;padding:32px'><h1>FinCrimeAI | Actual DuckDB schema</h1><p>Introspected tables and enforced constraints</p>"
            + tables.to_html(index=False)
            + constraints.to_html(index=False)
            + "</body></html>"
        )
        page.screenshot(path=str(images / "12_warehouse_schema.png"), full_page=True)
        manifest.append(
            {
                "file": "12_warehouse_schema.png",
                "source": "duckdb_constraints() and SHOW TABLES",
                "kind": "rendered live warehouse introspection",
            }
        )
        browser.close()
    for filename in ["05_confusion_matrix.png", "06_feature_importance.png"]:
        manifest.append(
            {
                "file": filename,
                "source": "fincrime_ai.reporting; measured model output",
                "kind": "generated analytical plot, not a UI screenshot",
            }
        )
    for item in manifest:
        item["sha256"] = hashlib.sha256(
            (images / item["file"]).read_bytes()
        ).hexdigest()
    (REPORTS / "screenshot_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Captured {len(manifest)} real screenshots/analytical evidence images")


if __name__ == "__main__":
    main()
