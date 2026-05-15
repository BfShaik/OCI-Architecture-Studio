from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PYTHON = REPO_ROOT / "app" / "backend" / ".venv" / "bin" / "python"

sys.path.append(str(REPO_ROOT / "knowledge" / "ingestion"))
sys.path.append(str(REPO_ROOT / "knowledge" / "refresh"))

import ingest  # noqa: E402
import ingest_releases  # noqa: E402


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")


def stable_release_key(release: dict[str, Any]) -> str:
    basis = "|".join(
        str(release.get(key, ""))
        for key in ("source_id", "title", "release_date", "service", "summary")
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def new_release_items(
    previous_snapshot: dict[str, Any],
    current_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    previous_keys = {
        stable_release_key(release)
        for release in previous_snapshot.get("releases", [])
        if isinstance(release, dict)
    }
    return [
        release
        for release in current_snapshot.get("releases", [])
        if isinstance(release, dict) and stable_release_key(release) not in previous_keys
    ]


def affected_source_ids(
    releases: list[dict[str, Any]],
    policy: dict[str, Any],
) -> list[str]:
    source_ids: set[str] = set()
    impact_map = policy.get("impact_to_source_ids", {})
    service_map = policy.get("service_to_source_ids", {})
    important_levels = set(policy.get("important_impact_levels", []))

    for release in releases:
        impact_level = str(release.get("impact_level", ""))
        tags = [str(tag) for tag in release.get("impact_tags", [])]
        services = [str(service) for service in release.get("services", [])]
        if release.get("service"):
            services.append(str(release["service"]))

        if impact_level in important_levels or tags:
            for tag in tags:
                source_ids.update(str(item) for item in impact_map.get(tag, []))
        for service in services:
            source_ids.update(str(item) for item in service_map.get(service, []))

    return sorted(source_ids)


def backup_file(path: Path, backup_dir: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / path.name
    shutil.copy2(path, target)
    return target


def build_release_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    release_args = argparse.Namespace(
        registry=args.release_registry,
        output=args.release_snapshot,
        timeout=args.timeout,
        min_fetched_words=args.min_fetched_words,
        max_source_chars=args.max_source_chars,
        max_items_per_source=args.max_items_per_source,
        no_fetch=args.no_fetch,
    )
    return ingest_releases.build_release_snapshot(release_args)


def build_selective_knowledge_index(
    args: argparse.Namespace,
    source_ids: list[str],
) -> dict[str, Any]:
    ingest_args = argparse.Namespace(
        registry=args.source_registry,
        output=args.knowledge_index,
        dimensions=args.dimensions,
        embedding_provider=args.embedding_provider,
        oci_region=args.oci_region,
        oci_profile=args.oci_profile,
        oci_auth_mode=args.oci_auth_mode,
        oci_genai_compartment_id=args.oci_genai_compartment_id,
        oci_genai_embedding_model_id=args.oci_genai_embedding_model_id,
        oci_genai_endpoint=args.oci_genai_endpoint,
        oci_namespace=args.oci_namespace,
        oci_upload_bucket=args.oci_upload_bucket,
        oci_upload_object=args.oci_upload_object,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        max_source_chars=args.max_source_chars,
        min_fetched_words=args.min_fetched_words,
        timeout=args.timeout,
        no_fetch=args.no_fetch,
        source_ids=source_ids,
        existing_index=args.knowledge_index,
    )
    index = ingest.build_index(ingest_args)
    return ingest.merge_with_existing_index(index, args.knowledge_index, source_ids)


def all_source_ids(source_registry: Path) -> list[str]:
    return [source["id"] for source in ingest.load_registry(source_registry)]


def run_gate(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def python_executable() -> str:
    return str(BACKEND_PYTHON if BACKEND_PYTHON.exists() else Path(sys.executable))


def run_post_refresh_gates(args: argparse.Namespace) -> list[dict[str, Any]]:
    python = python_executable()
    gates = [
        [python, "infra/scripts/check_retrieval_health.py", "--provider", "local_json"],
        [
            python,
            "infra/scripts/retrieval_regression_check.py",
            "--cases",
            "evals/golden-prompts.jsonl",
            "--cases",
            "evals/edge-cases.jsonl",
            "--output-dir",
            "evals/reports/retrieval-refresh",
        ],
        [python, "evals/run_golden.py", "--output-dir", "evals/reports/golden-refresh"],
        [
            python,
            "evals/run_golden.py",
            "--cases",
            "evals/edge-cases.jsonl",
            "--output-dir",
            "evals/reports/edge-refresh",
        ],
        [
            python,
            "evals/run_golden.py",
            "--cases",
            "evals/advisory-quality.jsonl",
            "--output-dir",
            "evals/reports/advisory-refresh",
        ],
        [
            python,
            "evals/run_golden.py",
            "--cases",
            "evals/orchestration-quality.jsonl",
            "--output-dir",
            "evals/reports/orchestration-refresh",
        ],
    ]
    if args.quick_gates:
        gates = gates[:2]
    return [run_gate(gate, REPO_ROOT) for gate in gates]


def restore_backups(backups: dict[str, Path | None], paths: dict[str, Path]) -> None:
    for key, backup in backups.items():
        if backup:
            shutil.copy2(backup, paths[key])


def execute_refresh_policy(args: argparse.Namespace) -> dict[str, Any]:
    policy = load_json(args.policy)
    started_at = datetime.now(UTC).isoformat()
    backup_dir = args.report_dir / "backups" / started_at.replace(":", "").replace("+", "Z")
    paths = {
        "knowledge_index": args.knowledge_index,
        "release_snapshot": args.release_snapshot,
    }
    backups = {
        "knowledge_index": backup_file(args.knowledge_index, backup_dir),
        "release_snapshot": backup_file(args.release_snapshot, backup_dir),
    }

    previous_release_snapshot = load_json(args.release_snapshot)
    current_release_snapshot = previous_release_snapshot
    changed_releases: list[dict[str, Any]] = []
    selected_source_ids: list[str] = []
    refresh_reason = args.mode

    if args.mode in {"release-watch", "manual"}:
        current_release_snapshot = build_release_snapshot(args)
        changed_releases = new_release_items(previous_release_snapshot, current_release_snapshot)
        selected_source_ids = affected_source_ids(changed_releases, policy)
        write_json(args.release_snapshot, current_release_snapshot)
        if not changed_releases and not args.force:
            refresh_reason = "release-watch-no-change"

    if args.mode == "stable-docs":
        selected_source_ids = all_source_ids(args.source_registry)
        refresh_reason = "stable-docs-cadence"

    if args.force and not selected_source_ids:
        selected_source_ids = all_source_ids(args.source_registry)
        refresh_reason = f"{args.mode}-forced"

    knowledge_index: dict[str, Any] | None = None
    if selected_source_ids:
        knowledge_index = build_selective_knowledge_index(args, selected_source_ids)
        write_json(args.knowledge_index, knowledge_index)

    gate_results: list[dict[str, Any]] = []
    if not args.skip_gates and selected_source_ids:
        gate_results = run_post_refresh_gates(args)

    passed = all(result["passed"] for result in gate_results) if gate_results else True
    upload_performed = False
    if passed and knowledge_index and args.oci_upload_bucket:
        ingest.upload_index_to_object_storage(knowledge_index, args)
        upload_performed = True
    if not passed and args.rollback_on_failure:
        restore_backups(backups, paths)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "started_at": started_at,
        "policy_version": policy.get("policy_version"),
        "mode": args.mode,
        "refresh_reason": refresh_reason,
        "cadence": policy.get("cadence", {}),
        "query_time_refresh": False,
        "changed_release_count": len(changed_releases),
        "changed_releases": changed_releases,
        "affected_source_ids": selected_source_ids,
        "selective_reindex": bool(selected_source_ids),
        "full_reindex": False,
        "knowledge_chunk_count": knowledge_index.get("chunk_count") if knowledge_index else None,
        "oci_upload_requested": bool(args.oci_upload_bucket),
        "oci_upload_performed": upload_performed,
        "gates": gate_results,
        "passed": passed,
        "rollback_performed": bool(not passed and args.rollback_on_failure),
        "backups": {key: str(value) if value else None for key, value in backups.items()},
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.report_dir / "knowledge-refresh-report.json", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCI Architecture Studio knowledge refresh policy.")
    parser.add_argument(
        "--mode",
        choices=("release-watch", "stable-docs", "manual"),
        default="release-watch",
    )
    parser.add_argument("--policy", type=Path, default=REPO_ROOT / "knowledge" / "refresh_policy.json")
    parser.add_argument("--source-registry", type=Path, default=REPO_ROOT / "knowledge" / "source_registry.json")
    parser.add_argument(
        "--release-registry",
        type=Path,
        default=REPO_ROOT / "knowledge" / "release_source_registry.json",
    )
    parser.add_argument(
        "--knowledge-index",
        type=Path,
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json",
    )
    parser.add_argument(
        "--release-snapshot",
        type=Path,
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-release-snapshot.json",
    )
    parser.add_argument("--report-dir", type=Path, default=REPO_ROOT / "knowledge" / "reports")
    parser.add_argument("--dimensions", type=int, default=256)
    parser.add_argument("--embedding-provider", choices=("local", "oci_genai"), default="local")
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal", "resource_principal"), default="config_file")
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-endpoint")
    parser.add_argument("--oci-namespace")
    parser.add_argument("--oci-upload-bucket")
    parser.add_argument("--oci-upload-object", default="knowledge/oci-rag-index.json")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=30)
    parser.add_argument("--max-source-chars", type=int, default=14000)
    parser.add_argument("--min-fetched-words", type=int, default=120)
    parser.add_argument("--max-items-per-source", type=int, default=12)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-gates", action="store_true")
    parser.add_argument("--quick-gates", action="store_true")
    parser.add_argument("--rollback-on-failure", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    report = execute_refresh_policy(parse_args())
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
