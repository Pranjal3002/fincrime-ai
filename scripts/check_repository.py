"""Check Git-visible files for accidental data, secrets and broken local doc links."""

import hashlib
import json
import re
import subprocess

from fincrime_ai.settings import REPORTS, ROOT


def main():
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    files = sorted(set(output.splitlines()))
    findings = []
    broken = []
    patterns = {
        "aws_access_key": r"\bAKIA[0-9A-Z]{16}\b",
        "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "github_token": r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
        "github_fine_grained_token": r"\bgithub_pat_[A-Za-z0-9_]{30,}\b",
        "aws_session_access_key": r"\bASIA[0-9A-Z]{16}\b",
        "openai_key": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b",
        "absolute_user_path": r"[A-Za-z]:[\\/]+Users[\\/]+[^\s\\/]+",
    }
    for relative in files:
        path = ROOT / relative
        if not path.is_file():
            continue
        if path.stat().st_size > 5_000_000:
            findings.append({"file": relative, "type": "over_5MB"})
        if (
            any(
                part
                in {
                    ".venv",
                    "__pycache__",
                    ".pytest_cache",
                    ".ruff_cache",
                    ".git",
                    "artifacts",
                    ".pbi",
                    "AnalysisServicesWorkspaces",
                    ".mypy_cache",
                    ".ipynb_checkpoints",
                    "node_modules",
                }
                for part in path.relative_to(ROOT).parts
            )
            or (path.name.startswith(".env") and path.name != ".env.example")
            or path.name == "secrets.toml"
            or path.suffix.lower() in {".duckdb", ".sqlite", ".joblib", ".log"}
        ):
            findings.append({"file": relative, "type": "unwanted_file"})
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".txt",
            ".toml",
            ".json",
            ".yml",
            ".yaml",
            ".sql",
            ".csv",
            ".bim",
            ".pbip",
            ".pbir",
            ".pbism",
            ".tmdl",
        }:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() in {".json", ".bim", ".pbip", ".pbir", ".pbism"}:
            try:
                json.loads(content)
            except json.JSONDecodeError:
                findings.append({"file": relative, "type": "invalid_json"})
        for kind, pattern in patterns.items():
            if re.search(pattern, content):
                findings.append({"file": relative, "type": kind})
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
                target = target.split("#")[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                if not (path.parent / target).exists():
                    broken.append({"file": relative, "target": target})
    image_count = 0
    image_hashes = set()
    for manifest_name in ("screenshot_manifest.json", "powerbi_evidence_manifest.json"):
        manifest = REPORTS / manifest_name
        if not manifest.exists():
            findings.append(
                {"file": str(manifest.relative_to(ROOT)), "type": "missing_manifest"}
            )
            continue
        for entry in json.loads(manifest.read_text(encoding="utf-8")):
            image = ROOT / "docs/images" / entry["file"]
            image_count += 1
            if not image.is_file():
                findings.append({"file": entry["file"], "type": "missing_evidence"})
                continue
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            if digest != entry["sha256"]:
                findings.append(
                    {"file": entry["file"], "type": "evidence_hash_mismatch"}
                )
            if digest in image_hashes:
                findings.append({"file": entry["file"], "type": "duplicate_evidence"})
            image_hashes.add(digest)
    result = {
        "git_visible_files": len(files),
        "file_bytes": sum(
            (ROOT / f).stat().st_size
            for f in files
            if (ROOT / f).is_file() and f != "reports/repository_checks.json"
        ),
        "file_bytes_excludes_this_report": True,
        "evidence_assets_checked": image_count,
        "secret_and_junk_findings": findings,
        "broken_local_markdown_links": broken,
        "scan_scope": "Git-visible text and BI source: heuristic secret/path/junk checks, JSON parsing, local Markdown file links and evidence hashes. Not a comprehensive security audit; anchors and external links are separate checks.",
    }
    (REPORTS / "repository_checks.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if findings or broken:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
