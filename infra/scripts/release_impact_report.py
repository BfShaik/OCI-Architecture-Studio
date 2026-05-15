from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(REPO_ROOT / "knowledge" / "refresh"))

from release_intelligence import impact_analysis, normalize_release_item  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def eval_case_paths() -> list[Path]:
    return [
        REPO_ROOT / "evals" / "golden-prompts.jsonl",
        REPO_ROOT / "evals" / "edge-cases.jsonl",
        REPO_ROOT / "evals" / "advisory-quality.jsonl",
        REPO_ROOT / "evals" / "orchestration-quality.jsonl",
        REPO_ROOT / "evals" / "vector-retrieval-cases.jsonl",
    ]


def write_report(report: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(report, indent=2) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report release intelligence impact without promoting snapshots.")
    parser.add_argument("--release-snapshot", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-release-snapshot.json")
    parser.add_argument("--knowledge-index", type=Path, default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json")
    parser.add_argument("--policy", type=Path, default=REPO_ROOT / "knowledge" / "refresh_policy.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    release_snapshot = load_json(args.release_snapshot)
    knowledge_index = load_json(args.knowledge_index)
    policy = load_json(args.policy)
    releases = [
        normalize_release_item(release)
        for release in release_snapshot.get("releases", [])[: args.limit]
        if isinstance(release, dict)
    ]
    impact = impact_analysis(
        releases=releases,
        knowledge_index=knowledge_index,
        eval_case_paths=eval_case_paths(),
        policy=policy,
    )
    report = {
        "status": "passed",
        "release_snapshot": str(args.release_snapshot),
        "knowledge_index": str(args.knowledge_index),
        "items_ingested": int(release_snapshot.get("release_count", len(release_snapshot.get("releases", [])))),
        "items_classified": len(releases),
        "impact": impact,
    }
    write_report(report, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
