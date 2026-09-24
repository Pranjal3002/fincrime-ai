"""Validate local PBIP references and relationship structure, not Desktop rendering."""

import json

from fincrime_ai.settings import REPORTS, ROOT


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    folder = ROOT / "dashboards/powerbi"
    stem = "FinCrimeAI_Financial_Crime_Analytics"
    project = read(folder / f"{stem}.pbip")
    for artifact in project["artifacts"]:
        report = folder / artifact["report"]["path"]
        reference = read(report / "definition.pbir")
        semantic = (report / reference["datasetReference"]["byPath"]["path"]).resolve()
        assert semantic.is_relative_to(folder.resolve()), "Reference outside BI source"
        assert (semantic / "definition.pbism").is_file()
    model = read(folder / f"{stem}.SemanticModel/model.bim")["model"]
    tables = {t["name"]: t for t in model["tables"]}
    assert len(tables) == len(model["tables"]), "Duplicate tables"
    relationships = model["relationships"]
    for rel in relationships:
        for side in ("from", "to"):
            table = tables[rel[f"{side}Table"]]
            assert rel[f"{side}Column"] in {c["name"] for c in table["columns"]}
        assert rel["fromCardinality"] == "many"
        assert rel["toCardinality"] == "one"
        assert rel["crossFilteringBehavior"] == "oneDirection"
        assert rel.get("isActive", True)
    definitions = folder / f"{stem}.Report/definition"
    pages = read(definitions / "pages/pages.json")
    for page in pages["pageOrder"]:
        assert (definitions / "pages" / page / "page.json").is_file()
    measures = sum(len(t.get("measures", [])) for t in tables.values())
    result = {
        "tables": len(tables),
        "active_one_to_many_single_direction_relationships": len(relationships),
        "dax_measure_definitions": measures,
        "experimental_page_definitions": len(pages["pageOrder"]),
        "project_references_resolve": True,
        "relationship_endpoints_resolve": True,
        "scope": "Static source validation only. Does not execute DAX, verify Desktop refresh or render report pages.",
    }
    (REPORTS / "powerbi_source_validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
