from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from oci_arch_studio_backend.services.evaluation_intelligence import (  # noqa: E402
    QualityGateThresholds,
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def thresholds_from_args(args: argparse.Namespace) -> QualityGateThresholds:
    config: dict[str, Any] = {}
    if args.thresholds:
        config = load_json(args.thresholds)
    return QualityGateThresholds(
        min_overall=float(config.get("min_overall", args.min_overall)),
        min_oci_specificity=float(config.get("min_oci_specificity", args.min_oci_specificity)),
        min_architecture_completeness=float(config.get("min_architecture_completeness", args.min_architecture_completeness)),
        min_tradeoff_quality=float(config.get("min_tradeoff_quality", args.min_tradeoff_quality)),
        max_high_hallucinations=int(config.get("max_high_hallucinations", args.max_high_hallucinations)),
        max_medium_hallucinations=int(config.get("max_medium_hallucinations", args.max_medium_hallucinations)),
    )


def evaluate_report(report: dict[str, Any], thresholds: QualityGateThresholds) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    cases = report.get("results", [])
    for case in cases:
        quality = case.get("architecture_quality", {})
        dimensions = quality.get("dimensions", {}) if isinstance(quality, dict) else {}
        hallucinations = quality.get("hallucination_findings", []) if isinstance(quality, dict) else []
        case_failures = []
        overall = float(quality.get("overall", 0.0)) if isinstance(quality.get("overall"), int | float) else 0.0
        if overall < thresholds.min_overall:
            case_failures.append(f"overall {overall} below {thresholds.min_overall}")
        for name, minimum in (
            ("oci_specificity", thresholds.min_oci_specificity),
            ("architecture_completeness", thresholds.min_architecture_completeness),
            ("tradeoff_quality", thresholds.min_tradeoff_quality),
        ):
            score = _dimension_score(dimensions, name)
            if score < minimum:
                case_failures.append(f"{name} {score} below {minimum}")
        high = sum(1 for finding in hallucinations if finding.get("severity") == "high")
        medium = sum(1 for finding in hallucinations if finding.get("severity") == "medium")
        if high > thresholds.max_high_hallucinations:
            case_failures.append(f"high hallucinations {high} above {thresholds.max_high_hallucinations}")
        if medium > thresholds.max_medium_hallucinations:
            case_failures.append(f"medium hallucinations {medium} above {thresholds.max_medium_hallucinations}")
        if case_failures:
            failures.append({"id": case.get("id"), "failures": case_failures})
    return {
        "status": "passed" if not failures else "failed",
        "case_count": len(cases),
        "failure_count": len(failures),
        "thresholds": thresholds.__dict__,
        "failures": failures,
    }


def _dimension_score(dimensions: dict[str, Any], name: str) -> float:
    value = dimensions.get(name, {})
    score = value.get("score") if isinstance(value, dict) else None
    return float(score) if isinstance(score, int | float) else 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate advisory eval reports on architecture-quality thresholds.")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--thresholds", type=Path)
    parser.add_argument("--min-overall", type=float, default=0.72)
    parser.add_argument("--min-oci-specificity", type=float, default=0.65)
    parser.add_argument("--min-architecture-completeness", type=float, default=0.65)
    parser.add_argument("--min-tradeoff-quality", type=float, default=0.55)
    parser.add_argument("--max-high-hallucinations", type=int, default=0)
    parser.add_argument("--max-medium-hallucinations", type=int, default=2)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_json(args.report)
    result = evaluate_report(report, thresholds_from_args(args))
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
