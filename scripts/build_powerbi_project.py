"""Author supported PBIP/PBIR and Tabular model sources; Desktop validates/saves PBIX."""

import json
import uuid

import pandas as pd

from fincrime_ai.settings import DATA, ROOT

NAME = "FinCrimeAI_Financial_Crime_Analytics"
BASE = ROOT / "dashboards/powerbi"
REPORT = BASE / f"{NAME}.Report"
MODEL = BASE / f"{NAME}.SemanticModel"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
MEASURES = {
    "Transactions Screened": ("COUNTROWS(fact_transactions)", "#,0"),
    "Review Alerts": ("COUNTROWS(fact_screening_alerts)", "#,0"),
    "Alert Rate": ("DIVIDE([Review Alerts], [Transactions Screened])", "0.00%"),
    "High-Risk Alerts": (
        "CALCULATE([Review Alerts], fact_screening_alerts[risk_score] >= 70)",
        "#,0",
    ),
    "Average Risk Score": ("AVERAGE(fact_transactions[risk_score])", "0.00"),
    "Total Amount GBP": ("SUM(fact_transactions[amount])", "£#,0"),
    "Average Amount GBP": ("AVERAGE(fact_transactions[amount])", "£#,0.00"),
    "Average Velocity": ("AVERAGE(fact_transactions[velocity_1h])", "0.00"),
    "Velocity Spike Payments": (
        "CALCULATE([Transactions Screened], fact_transactions[velocity_1h] >= 4)",
        "#,0",
    ),
    "Unusual-Time Payments": (
        "CALCULATE([Transactions Screened], fact_transactions[night] = 1)",
        "#,0",
    ),
    "Screening Alerts": (
        "CALCULATE([Transactions Screened], fact_transactions[screening_review] = 1)",
        "#,0",
    ),
    "Screening TP": (
        "CALCULATE([Transactions Screened], fact_transactions[screening_review] = 1, fact_transactions[screening_truth] = 1)",
        "#,0",
    ),
    "Screening FP": (
        "CALCULATE([Transactions Screened], fact_transactions[screening_review] = 1, fact_transactions[screening_truth] = 0)",
        "#,0",
    ),
    "Screening FN": (
        "CALCULATE([Transactions Screened], fact_transactions[screening_review] = 0, fact_transactions[screening_truth] = 1)",
        "#,0",
    ),
    "Screening TN": (
        "CALCULATE([Transactions Screened], fact_transactions[screening_review] = 0, fact_transactions[screening_truth] = 0)",
        "#,0",
    ),
    "Screening Precision": (
        "DIVIDE([Screening TP], [Screening TP] + [Screening FP])",
        "0.00%",
    ),
    "Screening Recall": (
        "DIVIDE([Screening TP], [Screening TP] + [Screening FN])",
        "0.00%",
    ),
    "Screening F1": (
        "DIVIDE(2 * [Screening Precision] * [Screening Recall], [Screening Precision] + [Screening Recall])",
        "0.00%",
    ),
    "Screening FPR": (
        "DIVIDE([Screening FP], [Screening FP] + [Screening TN])",
        "0.00%",
    ),
    "Screening FNR": (
        "DIVIDE([Screening FN], [Screening TP] + [Screening FN])",
        "0.00%",
    ),
    "Open Alerts": (
        'COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "OPEN"), 0)',
        "#,0",
    ),
    "In Review Alerts": (
        'COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "IN_REVIEW"), 0)',
        "#,0",
    ),
    "Escalated Alerts": (
        'COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "ESCALATED"), 0)',
        "#,0",
    ),
    "Closed Alerts": (
        'COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[status] = "CLOSED"), 0)',
        "#,0",
    ),
    "Reviewed False Positives": (
        'COALESCE(CALCULATE([Review Alerts], fact_screening_alerts[disposition] = "FALSE_POSITIVE"), 0)',
        "#,0",
    ),
    "Reviewed FP Share": (
        "DIVIDE([Reviewed False Positives], [Closed Alerts])",
        "0.00%",
    ),
    "Average Case Age at Cutoff": (
        "AVERAGE(fact_screening_alerts[age_at_data_cutoff_days])",
        "0.0",
    ),
    "Rule Alerts": ("COUNTROWS(bridge_alert_rules)", "#,0"),
    "XGBoost Threshold": (
        'CALCULATE(MAX(model_comparison[threshold]), model_comparison[model] = "XGBoost")',
        "0.00",
    ),
    "Test TP": (
        'CALCULATE(MAX(model_comparison[tp]), model_comparison[model] = "XGBoost")',
        "#,0",
    ),
    "Test FP": (
        'CALCULATE(MAX(model_comparison[fp]), model_comparison[model] = "XGBoost")',
        "#,0",
    ),
    "Test FN": (
        'CALCULATE(MAX(model_comparison[fn]), model_comparison[model] = "XGBoost")',
        "#,0",
    ),
    "Test TN": (
        'CALCULATE(MAX(model_comparison[tn]), model_comparison[model] = "XGBoost")',
        "#,0",
    ),
    "Cramers V": ("MAX(statistical_findings[cramers_v])", "0.000"),
    "Rank Biserial": ("MAX(statistical_findings[rank_biserial])", "0.000"),
    "Spearman Rho": ("MAX(statistical_findings[spearman_rho])", "0.000"),
    "Wilson Lower": ("MAX(statistical_findings[ci_lower])", "0.00%"),
    "Wilson Upper": ("MAX(statistical_findings[ci_upper])", "0.00%"),
}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def semantic_model():
    tables = []
    for path in sorted((DATA / "powerbi").glob("*.csv")):
        frame = pd.read_csv(path)
        cols = []
        transformations = []
        for col in frame.columns:
            series = frame[col]
            if col in {"timestamp", "calendar_date", "created_at", "reviewed_at"}:
                dtype, mtype = "dateTime", "type datetime"
            elif col in {"investigator_notes", "reason_code"}:
                dtype, mtype = "string", "type text"
            elif pd.api.types.is_bool_dtype(series):
                dtype, mtype = "boolean", "type logical"
            elif pd.api.types.is_integer_dtype(series):
                dtype, mtype = "int64", "Int64.Type"
            elif pd.api.types.is_float_dtype(series) and not series.isna().all():
                dtype, mtype = "double", "type number"
            else:
                dtype, mtype = "string", "type text"
            column = {
                "name": col,
                "dataType": dtype,
                "sourceColumn": col,
                "summarizeBy": "none",
                "lineageTag": str(uuid.uuid5(uuid.NAMESPACE_DNS, path.stem + col)),
            }
            if col.endswith("_key"):
                column["isHidden"] = True
            if col == "calendar_date":
                column.update({"formatString": "dd MMM yyyy", "isKey": True})
            if dtype == "double":
                column["formatString"] = (
                    "0.0000"
                    if col
                    in {
                        "precision",
                        "recall",
                        "f1",
                        "roc_auc",
                        "pr_auc_ap",
                        "threshold",
                    }
                    else "#,0.00"
                )
            cols.append(column)
            transformations.append('{"' + col + '", ' + mtype + "}")
        expression = [
            "let",
            f'    Source = Csv.Document(File.Contents(DataFolder & "\\{path.name}"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            "    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
            "    Types = Table.TransformColumnTypes(Headers, {"
            + ", ".join(transformations)
            + '}, "en-GB")',
            "in",
            "    Types",
        ]
        table = {
            "name": path.stem,
            "columns": cols,
            "partitions": [
                {
                    "name": path.stem,
                    "mode": "import",
                    "source": {"type": "m", "expression": expression},
                }
            ],
            "lineageTag": str(uuid.uuid5(uuid.NAMESPACE_DNS, path.stem)),
        }
        if path.stem == "dim_date":
            table["dataCategory"] = "Time"
        if path.stem == "fact_transactions":
            table["measures"] = [
                {
                    "name": name,
                    "expression": expr,
                    "formatString": fmt,
                    "displayFolder": "FinCrimeAI",
                    "description": "Synthetic simulation; human review remains final.",
                }
                for name, (expr, fmt) in MEASURES.items()
            ]
        tables.append(table)
    relationships = []
    dims = {
        "customer_key": ("dim_customer", "customer_key"),
        "counterparty_key": ("dim_counterparty", "counterparty_key"),
        "date_key": ("dim_date", "date_key"),
        "origin_geography_key": ("dim_origin_geography", "geography_key"),
        "destination_geography_key": ("dim_destination_geography", "geography_key"),
        "channel_key": ("dim_payment_channel", "channel_key"),
        "risk_key": ("dim_risk_category", "risk_key"),
    }
    for fact in ["fact_transactions", "fact_screening_alerts"]:
        for column, (dim, key) in dims.items():
            relationships.append(
                {
                    "name": f"{fact}_{column}",
                    "fromTable": fact,
                    "fromColumn": column,
                    "fromCardinality": "many",
                    "toTable": dim,
                    "toColumn": key,
                    "toCardinality": "one",
                    "crossFilteringBehavior": "oneDirection",
                    "isActive": True,
                }
            )
    relationships.append(
        {
            "name": "alert_rules",
            "fromTable": "bridge_alert_rules",
            "fromColumn": "alert_id",
            "fromCardinality": "many",
            "toTable": "fact_screening_alerts",
            "toColumn": "alert_id",
            "toCardinality": "one",
            "crossFilteringBehavior": "oneDirection",
            "isActive": True,
        }
    )
    model = {
        "name": NAME,
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-GB",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-GB",
            "expressions": [
                {
                    "name": "DataFolder",
                    "kind": "m",
                    "expression": '"C:\\FinCrimeAIData" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
                }
            ],
            "tables": tables,
            "relationships": relationships,
            "annotations": [
                {
                    "name": "PBI_QueryOrder",
                    "value": json.dumps(["DataFolder"] + [t["name"] for t in tables]),
                },
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
            ],
        },
    }
    save(MODEL / "model.bim", model)
    save(MODEL / "definition.pbism", {"version": "1.0", "settings": {}})
    save(
        BASE / "model_inventory.json",
        {
            "tables": [
                {"name": t["name"], "columns": len(t["columns"])} for t in tables
            ],
            "relationships": relationships,
            "measure_names": list(MEASURES),
        },
    )
    text = "# DAX measures\n\nThese definitions are generated with the semantic model. Desktop execution and validation are recorded separately in POWERBI_EVIDENCE.md.\n\n"
    text += "\n\n".join(
        f"### {name}\n\n```dax\n{name} =\n{expr}\n```\n\nFormat: `{fmt}`"
        for name, (expr, fmt) in MEASURES.items()
    )
    text += "\n\nBoth facts connect independently to shared dimensions with single-direction filtering. Review Alerts therefore respects date, channel, risk and both geography slicers. Screening rates use the filtered payment fact. Model/statistics benchmarks remain full-run. Age is days at the synthetic data cutoff, not current operational SLA. Blank Reviewed FP Share means no closed cases.\n"
    (BASE / "DAX_MEASURES.md").write_text(text, encoding="utf-8")


def lit(value):
    if isinstance(value, bool):
        value = "true" if value else "false"
    elif isinstance(value, str):
        value = "'" + value.replace("'", "''") + "'"
    else:
        value = str(value)
    return {"expr": {"Literal": {"Value": value}}}


def color(value):
    return {"solid": {"color": lit(value)}}


def field(table, column, kind="Column", aggregate=None):
    value = {kind: {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}
    if aggregate is not None:
        value = {"Aggregation": {"Expression": value, "Function": aggregate}}
    return {
        "field": value,
        "queryRef": f"{table}.{column}"
        + (f".{aggregate}" if aggregate is not None else ""),
        "nativeQueryRef": column,
    }


def measure(name):
    return field("fact_transactions", name, "Measure")


def visual(page, name, kind, x, y, w, h, title="", roles=None, objects=None):
    container = {
        "title": [
            {
                "properties": {
                    "show": lit(bool(title)),
                    "text": lit(title),
                    "fontSize": lit(12),
                    "fontColor": color("#102A43"),
                    "bold": lit(True),
                }
            }
        ],
        "background": [
            {
                "properties": {
                    "show": lit(True),
                    "color": color("#FFFFFF"),
                    "transparency": lit(0),
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": lit(True),
                    "color": color("#DFE7EF"),
                    "radius": lit(6),
                }
            }
        ],
        "visualHeader": [{"properties": {"show": lit(False)}}],
    }
    spec = {
        "visualType": kind,
        "visualContainerObjects": container,
        "drillFilterOtherVisuals": True,
    }
    if roles:
        spec["query"] = {
            "queryState": {
                role: {"projections": items} for role, items in roles.items()
            }
        }
    if objects:
        spec["objects"] = objects
    save(
        REPORT / f"definition/pages/{page}/visuals/{name}/visual.json",
        {
            "$schema": SCHEMA + "visualContainer/2.4.0/schema.json",
            "name": name,
            "position": {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "z": 0,
                "tabOrder": 0,
            },
            "visual": spec,
        },
    )


def textbox(page, name, text, x, y, w, h, size=14, bold=False):
    visual(
        page,
        name,
        "textbox",
        x,
        y,
        w,
        h,
        objects={
            "general": [
                {
                    "properties": {
                        "paragraphs": [
                            {
                                "textRuns": [
                                    {
                                        "value": text,
                                        "textStyle": {
                                            "fontFamily": "Segoe UI",
                                            "fontSize": f"{size}pt",
                                            "fontWeight": "bold" if bold else "normal",
                                            "color": "#102A43",
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        },
    )


def cards(page, items, y=112):
    width = (1536 - 12 * (len(items) - 1)) / len(items)
    for i, name in enumerate(items):
        visual(
            page,
            "card_" + str(i),
            "card",
            32 + i * (width + 12),
            y,
            width,
            100,
            title=name,
            roles={"Values": [measure(name)]},
            objects={
                "labels": [
                    {
                        "properties": {
                            "fontSize": lit(27),
                            "color": color("#087E8B"),
                            "labelDisplayUnits": lit(1),
                            "labelPrecision": lit(
                                2
                                if any(
                                    s in name
                                    for s in [
                                        "Rate",
                                        "Score",
                                        "Precision",
                                        "Recall",
                                        "F1",
                                        "FPR",
                                        "FNR",
                                        "Threshold",
                                        "Rho",
                                        "Biserial",
                                        "Cramers",
                                        "Wilson",
                                        "Age",
                                    ]
                                )
                                else 0
                            ),
                        }
                    }
                ],
                "categoryLabels": [{"properties": {"show": lit(False)}}],
            },
        )


def chart(
    page,
    name,
    title,
    table,
    column,
    m,
    y,
    x=32,
    w=752,
    h=270,
    kind="clusteredColumnChart",
):
    visual(
        page,
        name,
        kind,
        x,
        y,
        w,
        h,
        title,
        {"Category": [field(table, column)], "Y": [measure(m)]},
        objects={
            "dataPoint": [{"properties": {"defaultColor": color("#087E8B")}}],
            "categoryAxis": [{"properties": {"fontSize": lit(10)}}],
            "valueAxis": [{"properties": {"fontSize": lit(10)}}],
        },
    )


def table_visual(page, name, title, columns, x, y, w, h):
    visual(
        page,
        name,
        "tableEx",
        x,
        y,
        w,
        h,
        title,
        {"Values": columns},
        objects={
            "grid": [{"properties": {"rowPadding": lit(5)}}],
            "columnHeaders": [
                {
                    "properties": {
                        "fontSize": lit(11),
                        "fontColor": color("#102A43"),
                        "backColor": color("#EAF0F7"),
                    }
                }
            ],
            "values": [{"properties": {"fontSize": lit(10)}}],
        },
    )


def build_report():
    pages = [
        ("executive", "Executive Overview"),
        ("screening", "Screening Operations"),
        ("payment", "Payment Risk"),
        ("model", "Model Performance"),
        ("investigation", "Investigation Operations"),
        ("statistics", "Statistical Analysis"),
    ]
    save(
        BASE / f"{NAME}.pbip",
        {
            "version": "1.0",
            "artifacts": [{"report": {"path": REPORT.name}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    save(
        REPORT / "definition.pbir",
        {
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../" + MODEL.name}},
        },
    )
    save(
        REPORT / "definition/version.json",
        {"$schema": SCHEMA + "versionMetadata/1.0.0/schema.json", "version": "4.0.0"},
    )
    save(
        REPORT / "definition/report.json",
        {
            "$schema": SCHEMA + "report/2.0.0/schema.json",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU06",
                    "reportVersionAtImport": "5.55",
                    "type": "SharedResources",
                }
            },
            "settings": {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": "AllowSummarized",
                "defaultDrillFilterOtherVisuals": True,
            },
        },
    )
    save(
        REPORT / "definition/pages/pages.json",
        {
            "$schema": SCHEMA + "pagesMetadata/1.0.0/schema.json",
            "pageOrder": [p for p, _ in pages],
            "activePageName": "executive",
        },
    )
    for page, title in pages:
        save(
            REPORT / f"definition/pages/{page}/page.json",
            {
                "$schema": SCHEMA + "page/2.0.0/schema.json",
                "name": page,
                "displayName": title,
                "displayOption": "FitToPage",
                "width": 1600,
                "height": 1000,
                "objects": {
                    "background": [
                        {
                            "properties": {
                                "color": color("#F3F6FA"),
                                "transparency": lit(0),
                            }
                        }
                    ]
                },
            },
        )
        textbox(page, "header", "FinCrimeAI  |  " + title, 32, 16, 1536, 52, 26, True)
        subtitle = (
            "Synthetic Financial Crime Screening Simulation"
            if page == "executive"
            else (
                "Synthetic held-out evaluation | selected model: XGBoost"
                if page == "model"
                else "Synthetic data | evidence-led analytics | human review remains final"
            )
        )
        textbox(page, "subtitle", subtitle, 32, 70, 1536, 32, 12)
        textbox(
            page,
            "footer",
            "Educational portfolio simulation. Not intended for production compliance, AML or sanctions decisioning. All amounts GBP. Human review required.",
            32,
            957,
            1536,
            29,
            10,
        )
    p = "executive"
    cards(
        p,
        [
            "Transactions Screened",
            "Review Alerts",
            "Alert Rate",
            "High-Risk Alerts",
            "Average Risk Score",
            "Screening Precision",
            "Screening Recall",
        ],
    )
    for i, (t, c, label) in enumerate(
        [
            ("dim_date", "calendar_date", "Date"),
            ("dim_payment_channel", "payment_channel", "Payment channel"),
            ("dim_risk_category", "risk_category", "Risk category"),
            ("dim_origin_geography", "country_code", "Origin"),
            ("dim_destination_geography", "country_code", "Destination"),
        ]
    ):
        visual(
            p,
            "slicer_" + str(i),
            "slicer",
            32 + i * 309,
            228,
            296,
            75,
            label,
            {"Values": [field(t, c)]},
            objects={
                "data": [{"properties": {"mode": lit("Dropdown")}}],
                "selection": [{"properties": {"singleSelect": lit(False)}}],
            },
        )
    chart(
        p,
        "trend",
        "Review alerts by day",
        "dim_date",
        "calendar_date",
        "Review Alerts",
        318,
        h=282,
        kind="lineChart",
    )
    chart(
        p,
        "risk",
        "Alerts by rule-risk category",
        "dim_risk_category",
        "risk_category",
        "Review Alerts",
        318,
        x=800,
        w=368,
        h=282,
    )
    chart(
        p,
        "status",
        "Actual case status",
        "fact_screening_alerts",
        "status",
        "Review Alerts",
        318,
        x=1184,
        w=384,
        h=282,
    )
    chart(
        p,
        "channel",
        "Alerts by payment channel",
        "dim_payment_channel",
        "payment_channel",
        "Review Alerts",
        616,
        w=496,
        h=320,
    )
    chart(
        p,
        "origin",
        "Alerts by origin",
        "dim_origin_geography",
        "country_code",
        "Review Alerts",
        616,
        x=544,
        w=496,
        h=320,
    )
    chart(
        p,
        "destination",
        "Alerts by destination | XZ/QZ fictional",
        "dim_destination_geography",
        "country_code",
        "Review Alerts",
        616,
        x=1056,
        w=512,
        h=320,
    )
    p = "screening"
    cards(
        p,
        [
            "Screening Alerts",
            "Screening Precision",
            "Screening Recall",
            "Screening F1",
            "Screening FPR",
            "Screening FNR",
        ],
    )
    chart(
        p,
        "scores",
        "Screening scores | 10-point bins",
        "fact_transactions",
        "screening_score_band",
        "Transactions Screened",
        232,
        w=496,
        h=260,
    )
    chart(
        p,
        "method",
        "Review matches by method",
        "dim_counterparty",
        "match_method",
        "Screening Alerts",
        232,
        x=544,
        w=496,
        h=260,
    )
    chart(
        p,
        "risk",
        "Alerts by beneficiary baseline risk",
        "dim_counterparty",
        "baseline_risk",
        "Review Alerts",
        232,
        x=1056,
        w=512,
        h=260,
    )
    chart(
        p,
        "rules",
        "Triggered controls | one alert can trigger several",
        "bridge_alert_rules",
        "rule_name",
        "Rule Alerts",
        510,
        w=600,
        h=427,
        kind="clusteredBarChart",
    )
    table_visual(
        p,
        "details",
        "Screening evidence and current case status",
        [
            field("fact_screening_alerts", "transaction_id"),
            field("dim_counterparty", "counterparty_name"),
            field("dim_counterparty", "screening_score"),
            field("dim_counterparty", "matched_entity"),
            field("dim_counterparty", "name_similarity_score"),
            field("dim_counterparty", "reason_codes"),
            field("fact_screening_alerts", "status"),
        ],
        648,
        510,
        920,
        427,
    )
    p = "payment"
    cards(
        p,
        [
            "Total Amount GBP",
            "Average Amount GBP",
            "Average Velocity",
            "Velocity Spike Payments",
            "Unusual-Time Payments",
        ],
    )
    chart(
        p,
        "amounts",
        "Payment amount distribution (GBP bands)",
        "fact_transactions",
        "amount_band",
        "Transactions Screened",
        232,
        w=496,
        h=260,
    )
    visual(
        p,
        "scatter",
        "scatterChart",
        544,
        232,
        496,
        260,
        "Amount vs rule score | visual samples payments",
        {
            "Category": [field("fact_transactions", "transaction_id")],
            "X": [field("fact_transactions", "amount", aggregate=0)],
            "Y": [field("fact_transactions", "risk_score", aggregate=0)],
        },
    )
    chart(
        p,
        "highrisk",
        "High-risk review alerts by destination",
        "dim_destination_geography",
        "country_code",
        "High-Risk Alerts",
        232,
        x=1056,
        w=512,
        h=260,
    )
    chart(
        p,
        "channel",
        "Alert rate by channel",
        "dim_payment_channel",
        "payment_channel",
        "Alert Rate",
        510,
        w=496,
        h=260,
    )
    chart(
        p,
        "type",
        "Payment counts by type",
        "fact_transactions",
        "payment_type",
        "Transactions Screened",
        510,
        x=544,
        w=496,
        h=260,
    )
    chart(
        p,
        "hours",
        "Payments by UTC hour",
        "fact_transactions",
        "hour_utc",
        "Transactions Screened",
        510,
        x=1056,
        w=512,
        h=260,
    )
    chart(
        p,
        "unusual",
        "Unusual-time payments over the observation window",
        "dim_date",
        "calendar_date",
        "Unusual-Time Payments",
        788,
        w=1536,
        h=149,
        kind="lineChart",
    )
    p = "model"
    cards(p, ["XGBoost Threshold", "Test TP", "Test FP", "Test FN", "Test TN"])
    table_visual(
        p,
        "comparison",
        "Held-out model comparison | PR-AUC means average precision",
        [
            field("model_comparison", c)
            for c in ["model", "precision", "recall", "f1", "roc_auc", "pr_auc_ap"]
        ],
        32,
        230,
        920,
        238,
    )
    textbox(
        p,
        "evaluation_note",
        "60,000 train / 20,000 validation / 20,000 test\nSelection: minimum validation cost 5 × FN + FP.\n927 missed synthetic positives; 1,204 false positives.\nOperational slicers do not change held-out benchmarks.",
        968,
        230,
        600,
        238,
        17,
    )
    visual(
        p,
        "importance",
        "clusteredBarChart",
        32,
        486,
        752,
        452,
        "Selected XGBoost | global feature importance",
        {
            "Category": [field("feature_importance", "feature")],
            "Y": [field("feature_importance", "importance", aggregate=0)],
        },
    )
    visual(
        p,
        "threshold",
        "lineChart",
        800,
        486,
        768,
        452,
        "Validation threshold cost | 5 × FN + FP",
        {
            "Category": [field("threshold_analysis", "threshold")],
            "Y": [
                field("threshold_analysis", "validation_cost_5fn_plus_fp", aggregate=0)
            ],
            "Series": [field("threshold_analysis", "model")],
        },
    )
    p = "investigation"
    cards(
        p,
        [
            "Open Alerts",
            "In Review Alerts",
            "Escalated Alerts",
            "Closed Alerts",
            "Reviewed False Positives",
            "Average Case Age at Cutoff",
        ],
    )
    textbox(
        p,
        "note",
        "All current cases are OPEN. No human disposition history has been invented. Age is measured at the synthetic data cutoff (31 March 2026), not a real operational SLA.",
        32,
        230,
        1536,
        54,
        13,
    )
    chart(
        p,
        "status",
        "Cases by status",
        "fact_screening_alerts",
        "status",
        "Review Alerts",
        300,
        w=400,
        h=255,
    )
    chart(
        p,
        "disposition",
        "Disposition | NOT_REVIEWED is a missing-state label",
        "fact_screening_alerts",
        "disposition",
        "Review Alerts",
        300,
        x=448,
        w=480,
        h=255,
    )
    chart(
        p,
        "trend",
        "Investigation volume by payment date",
        "dim_date",
        "calendar_date",
        "Review Alerts",
        300,
        x=944,
        w=624,
        h=255,
        kind="lineChart",
    )
    table_visual(
        p,
        "cases",
        "Case explorer | scores, reasons and review status",
        [
            field("fact_screening_alerts", c)
            for c in [
                "alert_id",
                "transaction_id",
                "risk_score",
                "rules_triggered",
                "status",
                "age_at_data_cutoff_days",
            ]
        ],
        32,
        572,
        1536,
        364,
    )
    p = "statistics"
    cards(
        p,
        ["Cramers V", "Rank Biserial", "Spearman Rho", "Wilson Lower", "Wilson Upper"],
    )
    textbox(
        p,
        "interpretation",
        "Exploratory full-run statistics. Amount and geography partly define alerts; repeated customer payments violate independence assumptions. Effect sizes describe association, not causality. Small p-values do not establish business value.",
        32,
        230,
        1536,
        82,
        15,
    )
    chart(
        p,
        "amounts",
        "Transaction amount distribution (GBP bands)",
        "fact_transactions",
        "amount_band",
        "Transactions Screened",
        330,
        w=752,
        h=280,
    )
    chart(
        p,
        "geography",
        "Observed alert rate by destination",
        "dim_destination_geography",
        "country_code",
        "Alert Rate",
        330,
        x=800,
        w=768,
        h=280,
    )
    table_visual(
        p,
        "tests",
        "Measured hypothesis tests and amount comparison",
        [
            field("statistical_findings", c)
            for c in [
                "chi_square",
                "chi_p_value",
                "mann_whitney_u",
                "alerted_median",
                "nonalerted_median",
            ]
        ],
        32,
        628,
        1536,
        160,
    )
    textbox(
        p,
        "test_note",
        "Chi-square: geography vs alerts; minimum expected cell count 5,671.08.\nMann–Whitney compares amount distributions. Median alerted payment £2,224.15; non-alerted £676.685.\nMann–Whitney and Spearman p-values underflow to zero in the source; this does not mean an impossible null.",
        32,
        804,
        1536,
        134,
        15,
    )
    theme = {
        "name": "FinCrimeAI Enterprise",
        "dataColors": [
            "#087E8B",
            "#214D72",
            "#5C9EAD",
            "#DCA64C",
            "#64748B",
            "#9BC4CB",
        ],
        "background": "#F3F6FA",
        "foreground": "#102A43",
        "tableAccent": "#087E8B",
        "textClasses": {
            "title": {"fontFace": "Segoe UI", "color": "#102A43"},
            "label": {"fontFace": "Segoe UI", "color": "#334E68"},
            "callout": {"fontFace": "Segoe UI", "color": "#087E8B"},
        },
    }
    save(BASE / "FinCrimeAI_Theme.json", theme)


if __name__ == "__main__":
    semantic_model()
    build_report()
    print(
        "Authored Power BI project sources. Desktop refresh/open validation is still required."
    )
