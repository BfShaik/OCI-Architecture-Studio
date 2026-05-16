from __future__ import annotations

import argparse
import hashlib
import json
import os
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
from release_intelligence import apply_release_overlay, impact_analysis, normalize_release_item  # noqa: E402


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


def snapshot_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_run_id(started_at: str) -> str:
    compact = (
        started_at.replace("+00:00", "Z")
        .replace("-", "")
        .replace(":", "")
        .replace(".", "")
    )
    return f"refresh-{compact}"


def version_id(prefix: str, payload: dict[str, Any]) -> str:
    generated_at = str(payload.get("generated_at") or datetime.now(UTC).isoformat())
    compact = generated_at.replace("+00:00", "Z").replace("-", "").replace(":", "").replace(".", "")
    return f"{prefix}-{compact}-{snapshot_hash(payload)[:10]}"


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


def default_eval_case_paths() -> list[Path]:
    return [
        REPO_ROOT / "evals" / "golden-prompts.jsonl",
        REPO_ROOT / "evals" / "edge-cases.jsonl",
        REPO_ROOT / "evals" / "advisory-quality.jsonl",
        REPO_ROOT / "evals" / "orchestration-quality.jsonl",
        REPO_ROOT / "evals" / "vector-retrieval-cases.jsonl",
    ]


def backup_file(path: Path, backup_dir: Path) -> Path | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / path.name
    shutil.copy2(path, target)
    return target


def preserve_historical_snapshot(path: Path, historical_dir: Path, *, valid_to: str, snapshot_type: str) -> Path | None:
    if not path.exists():
        return None
    historical_dir.mkdir(parents=True, exist_ok=True)
    payload = load_json(path)
    payload["snapshot_scope"] = "historical"
    payload["knowledge_scope"] = "historical"
    payload["valid_to"] = valid_to
    payload["source_snapshot_path"] = str(path)
    payload["snapshot_type"] = snapshot_type
    target = historical_dir / f"historical-{snapshot_type}-{valid_to.replace(':', '').replace('-', '')}.json"
    write_json(target, payload)
    return target


def promote_candidate(candidate: Path, authoritative: Path, backup_dir: Path) -> Path | None:
    backup = backup_file(authoritative, backup_dir)
    authoritative.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidate, authoritative)
    return backup


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
    existing_index_path: Path | None = None,
) -> dict[str, Any]:
    ingest_args = argparse.Namespace(
        registry=args.source_registry,
        output=args.knowledge_index,
        dimensions=args.dimensions,
        embedding_provider=args.embedding_provider,
        embedding_fallback_enabled=args.embedding_fallback_enabled,
        oci_region=args.oci_region,
        oci_profile=args.oci_profile,
        oci_auth_mode=args.oci_auth_mode,
        oci_genai_compartment_id=args.oci_genai_compartment_id,
        oci_genai_embedding_model_id=args.oci_genai_embedding_model_id,
        oci_genai_embedding_dimensions=args.oci_genai_embedding_dimensions,
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
        existing_index=existing_index_path or args.knowledge_index,
    )
    index = ingest.build_index(ingest_args)
    return ingest.merge_with_existing_index(index, existing_index_path or args.knowledge_index, source_ids)


def retag_existing_knowledge_index(
    knowledge_index_path: Path,
    releases: list[dict[str, Any]],
    impact: dict[str, Any],
) -> dict[str, Any]:
    knowledge_index = load_json(knowledge_index_path)
    return apply_release_overlay(knowledge_index, releases, impact)


def all_source_ids(source_registry: Path) -> list[str]:
    return [source["id"] for source in ingest.load_registry(source_registry)]


def run_gate(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
        env=env,
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


def run_post_refresh_gates(
    args: argparse.Namespace,
    candidate_knowledge_index: Path,
    candidate_release_snapshot: Path,
    run_report_dir: Path,
) -> list[dict[str, Any]]:
    python = python_executable()
    gate_env = {
        **os.environ,
        "KNOWLEDGE_INDEX_PATH": str(candidate_knowledge_index),
        "RELEASE_SNAPSHOT_PATH": str(candidate_release_snapshot),
        "RETRIEVAL_PROVIDER": "local_json",
    }
    gates = [
        [
            python,
            "infra/scripts/check_retrieval_health.py",
            "--provider",
            "local_json",
            "--index-path",
            str(candidate_knowledge_index),
        ],
        [
            python,
            "infra/scripts/retrieval_regression_check.py",
            "--cases",
            "evals/golden-prompts.jsonl",
            "--cases",
            "evals/edge-cases.jsonl",
            "--output-dir",
            str(run_report_dir / "retrieval-regression"),
            "--index-path",
            str(candidate_knowledge_index),
        ],
        [python, "evals/run_golden.py", "--output-dir", str(run_report_dir / "golden")],
        [
            python,
            "evals/run_golden.py",
            "--cases",
            "evals/edge-cases.jsonl",
            "--output-dir",
            str(run_report_dir / "edge"),
        ],
        [
            python,
            "evals/run_golden.py",
            "--cases",
            "evals/advisory-quality.jsonl",
            "--output-dir",
            str(run_report_dir / "advisory"),
        ],
        [
            python,
            "evals/run_golden.py",
            "--cases",
            "evals/orchestration-quality.jsonl",
            "--output-dir",
            str(run_report_dir / "orchestration"),
        ],
    ]
    if args.quick_gates:
        gates = gates[:2]
    return [run_gate(gate, REPO_ROOT, env=gate_env) for gate in gates]


def restore_backups(backups: dict[str, Path | None], paths: dict[str, Path]) -> None:
    for key, backup in backups.items():
        if backup:
            shutil.copy2(backup, paths[key])


def load_status(report_dir: Path) -> dict[str, Any]:
    return load_json(report_dir / "knowledge-refresh-status.json")


def write_status(report_dir: Path, status: dict[str, Any]) -> None:
    write_json(report_dir / "knowledge-refresh-status.json", status)


def candidate_args(args: argparse.Namespace, knowledge_index: Path, release_snapshot: Path) -> argparse.Namespace:
    values = vars(args).copy()
    values["knowledge_index"] = knowledge_index
    values["release_snapshot"] = release_snapshot
    return argparse.Namespace(**values)


def write_manifest(
    path: Path,
    *,
    run_id: str,
    started_at: str,
    policy: dict[str, Any],
    mode: str,
    refresh_reason: str,
    status: str,
    knowledge_index: dict[str, Any] | None,
    release_snapshot: dict[str, Any],
    affected_source_ids: list[str],
    changed_releases: list[dict[str, Any]],
    gates: list[dict[str, Any]],
    candidate_paths: dict[str, Path],
    promoted_paths: dict[str, Path],
    rollback_sources: dict[str, Path | None] | None = None,
    impact_report: dict[str, Any] | None = None,
    historical_snapshots: dict[str, Path | None] | None = None,
) -> dict[str, Any]:
    manifest = {
        "run_id": run_id,
        "started_at": started_at,
        "generated_at": datetime.now(UTC).isoformat(),
        "policy_version": policy.get("policy_version"),
        "mode": mode,
        "refresh_reason": refresh_reason,
        "status": status,
        "lineage": {
            "knowledge_snapshot_version": version_id("knowledge", knowledge_index) if knowledge_index else None,
            "release_snapshot_version": version_id("release", release_snapshot),
            "embedding_version": (knowledge_index or {}).get("embedding_model"),
            "embedding_provider": (knowledge_index or {}).get("embedding_provider"),
            "metadata_schema_version": (knowledge_index or {}).get("metadata_schema_version"),
            "affected_source_ids": affected_source_ids,
            "changed_release_ids": [str(item.get("id") or item.get("title")) for item in changed_releases],
            "impacted_eval_cases": sorted((impact_report or {}).get("impacted_eval_cases", {}).keys()),
        },
        "impact_report": impact_report or {},
        "candidate_paths": {key: str(value) for key, value in candidate_paths.items()},
        "promoted_paths": {key: str(value) for key, value in promoted_paths.items()},
        "historical_snapshots": {
            key: str(value) if value else None for key, value in (historical_snapshots or {}).items()
        },
        "rollback_sources": {
            key: str(value) if value else None for key, value in (rollback_sources or {}).items()
        },
        "gates": gates,
    }
    write_json(path, manifest)
    return manifest


def update_status_from_report(
    args: argparse.Namespace,
    report: dict[str, Any],
    manifest: dict[str, Any],
    previous_status: dict[str, Any],
) -> None:
    history = list(previous_status.get("history", []))
    history.append(
        {
            "run_id": report["run_id"],
            "generated_at": report["generated_at"],
            "status": report["status"],
            "passed": report["passed"],
            "refresh_reason": report["refresh_reason"],
            "affected_source_ids": report["affected_source_ids"],
            "gate_failures": [
                gate["command"] for gate in report.get("gates", []) if not gate.get("passed")
            ],
        }
    )
    promoted = report["status"] == "promoted"
    status = {
        "generated_at": datetime.now(UTC).isoformat(),
        "last_run": {
            "run_id": report["run_id"],
            "status": report["status"],
            "passed": report["passed"],
            "started_at": report["started_at"],
            "generated_at": report["generated_at"],
            "changed_release_count": report["changed_release_count"],
            "affected_source_ids": report["affected_source_ids"],
            "gates_passed": report["gates_passed"],
            "rollback_performed": report["rollback_performed"],
            "lifecycle": report.get("lifecycle", {}),
        },
        "current_promoted_snapshot": (
            manifest if promoted else previous_status.get("current_promoted_snapshot")
        ),
        "previous_promoted_snapshot": (
            previous_status.get("current_promoted_snapshot")
            if promoted
            else previous_status.get("previous_promoted_snapshot")
        ),
        "last_rollback": previous_status.get("last_rollback"),
        "history": history[-25:],
    }
    write_status(args.report_dir, status)


def build_refresh_lifecycle(report: dict[str, Any], *, candidate_changed: bool) -> dict[str, Any]:
    gates = report.get("gates", [])
    rollback_sources = report.get("rollback_sources", {})
    promoted = bool(report.get("promoted"))
    oci_upload_requested = bool(report.get("oci_upload_requested"))
    oci_upload_performed = bool(report.get("oci_upload_performed"))

    if promoted:
        promotion_status = "promoted"
    elif candidate_changed and report.get("gates_passed") is False:
        promotion_status = "blocked_by_gates"
    elif candidate_changed:
        promotion_status = "validated_without_promotion"
    else:
        promotion_status = "no_change"

    return {
        "candidate_created": bool(report.get("candidate_paths")),
        "candidate_changed": candidate_changed,
        "gates_run": bool(gates),
        "gates_passed": bool(report.get("gates_passed")),
        "promoted": promoted,
        "promotion_status": promotion_status,
        "authoritative_snapshots_updated": promoted,
        "oci_upload_requested": oci_upload_requested,
        "oci_upload_performed": oci_upload_performed,
        "oci_upload_status": (
            "uploaded"
            if oci_upload_performed
            else "requested_not_performed"
            if oci_upload_requested
            else "not_requested"
        ),
        "rollback_available": any(rollback_sources.values()),
        "rollback_performed": bool(report.get("rollback_performed")),
        "query_time_refresh": bool(report.get("query_time_refresh")),
        "selective_reindex": bool(report.get("selective_reindex")),
        "full_reindex": bool(report.get("full_reindex")),
    }


def rollback_latest(args: argparse.Namespace) -> dict[str, Any]:
    status = load_status(args.report_dir)
    current = status.get("current_promoted_snapshot") or {}
    rollback_sources = current.get("rollback_sources") or {}
    targets = {
        "knowledge_index": args.knowledge_index,
        "release_snapshot": args.release_snapshot,
    }
    restored: dict[str, str] = {}
    for key, target in targets.items():
        source = rollback_sources.get(key)
        if source and Path(source).exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(source), target)
            restored[key] = str(source)

    rollback_event = {
        "run_id": make_run_id(datetime.now(UTC).isoformat()),
        "generated_at": datetime.now(UTC).isoformat(),
        "rolled_back_from": current.get("run_id"),
        "restored": restored,
        "passed": bool(restored),
    }
    if restored:
        status["current_promoted_snapshot"] = status.get("previous_promoted_snapshot")
        status["previous_promoted_snapshot"] = None
    status["last_rollback"] = rollback_event
    history = list(status.get("history", []))
    history.append(
        {
            "run_id": rollback_event["run_id"],
            "generated_at": rollback_event["generated_at"],
            "status": "rollback",
            "passed": bool(restored),
            "refresh_reason": "operator-rollback",
            "affected_source_ids": [],
            "gate_failures": [],
        }
    )
    status["history"] = history[-25:]
    write_status(args.report_dir, status)
    write_json(args.report_dir / "knowledge-refresh-rollback-report.json", rollback_event)
    return rollback_event


def execute_refresh_policy(args: argparse.Namespace) -> dict[str, Any]:
    policy = load_json(args.policy)
    started_at = datetime.now(UTC).isoformat()
    run_id = make_run_id(started_at)
    run_dir = args.report_dir / "runs" / run_id
    candidate_dir = run_dir / "candidates"
    backup_dir = run_dir / "rollback"
    gate_report_dir = run_dir / "gates"
    candidate_knowledge_path = candidate_dir / args.knowledge_index.name
    candidate_release_path = candidate_dir / args.release_snapshot.name
    previous_status = load_status(args.report_dir)

    previous_release_snapshot = load_json(args.release_snapshot)
    current_release_snapshot = previous_release_snapshot
    changed_releases: list[dict[str, Any]] = []
    normalized_changed_releases: list[dict[str, Any]] = []
    selected_source_ids: list[str] = []
    refresh_reason = args.mode
    impact_report: dict[str, Any] = {}

    if args.mode in {"release-watch", "manual"}:
        current_release_snapshot = build_release_snapshot(
            candidate_args(args, candidate_knowledge_path, candidate_release_path)
        )
        changed_releases = new_release_items(previous_release_snapshot, current_release_snapshot)
        normalized_changed_releases = [normalize_release_item(release) for release in changed_releases]
        existing_index = load_json(args.knowledge_index)
        impact_report = impact_analysis(
            releases=normalized_changed_releases,
            knowledge_index=existing_index,
            eval_case_paths=default_eval_case_paths(),
            policy=policy,
        )
        selected_source_ids = sorted(set(affected_source_ids(normalized_changed_releases, policy)) | set(impact_report.get("affected_source_ids", [])))
        if not changed_releases and not args.force:
            refresh_reason = "release-watch-no-change"

    if args.mode == "stable-docs":
        selected_source_ids = all_source_ids(args.source_registry)
        refresh_reason = "stable-docs-cadence"

    if args.force and not selected_source_ids:
        selected_source_ids = all_source_ids(args.source_registry)
        refresh_reason = f"{args.mode}-forced"
        impact_report = {
            "release_count": len(normalized_changed_releases),
            "affected_source_ids": selected_source_ids,
            "affected_chunk_ids": [],
            "change_categories": [],
            "impacted_eval_cases": {},
            "refresh_actions": ["full_reindex"],
            "regression_required": True,
            "unresolved_risks": [],
        }

    candidate_dir.mkdir(parents=True, exist_ok=True)
    if current_release_snapshot or not args.release_snapshot.exists():
        write_json(candidate_release_path, current_release_snapshot)
    elif args.release_snapshot.exists():
        shutil.copy2(args.release_snapshot, candidate_release_path)
    if args.knowledge_index.exists():
        shutil.copy2(args.knowledge_index, candidate_knowledge_path)

    knowledge_index: dict[str, Any] | None = None
    if selected_source_ids:
        knowledge_index = build_selective_knowledge_index(
            candidate_args(args, candidate_knowledge_path, candidate_release_path),
            selected_source_ids,
            existing_index_path=args.knowledge_index,
        )
        if normalized_changed_releases:
            knowledge_index = apply_release_overlay(knowledge_index, normalized_changed_releases, impact_report)
        write_json(candidate_knowledge_path, knowledge_index)
    else:
        knowledge_index = load_json(candidate_knowledge_path)
        if normalized_changed_releases and impact_report.get("metadata_update_required"):
            knowledge_index = apply_release_overlay(knowledge_index, normalized_changed_releases, impact_report)
            write_json(candidate_knowledge_path, knowledge_index)

    gate_results: list[dict[str, Any]] = []
    candidate_changed = bool(selected_source_ids or changed_releases or args.force)
    if not args.skip_gates and candidate_changed:
        gate_results = run_post_refresh_gates(
            args,
            candidate_knowledge_path,
            candidate_release_path,
            gate_report_dir,
        )

    passed = all(result["passed"] for result in gate_results) if gate_results else True
    upload_performed = False
    promoted = False
    rollback_sources: dict[str, Path | None] = {}
    manifest = write_manifest(
        run_dir / "manifest.json",
        run_id=run_id,
        started_at=started_at,
        policy=policy,
        mode=args.mode,
        refresh_reason=refresh_reason,
        status="candidate_validated" if passed else "candidate_failed",
        knowledge_index=knowledge_index,
        release_snapshot=current_release_snapshot,
        affected_source_ids=selected_source_ids,
        changed_releases=changed_releases,
        gates=gate_results,
        impact_report=impact_report,
        candidate_paths={
            "knowledge_index": candidate_knowledge_path,
            "release_snapshot": candidate_release_path,
        },
        promoted_paths={
            "knowledge_index": args.knowledge_index,
            "release_snapshot": args.release_snapshot,
        },
    )

    if passed and knowledge_index and args.oci_upload_bucket:
        ingest.upload_index_to_object_storage(knowledge_index, args)
        upload_performed = True

    if passed and candidate_changed:
        historical_snapshots = {
            "knowledge_index": preserve_historical_snapshot(
                args.knowledge_index,
                args.release_snapshot.parent / "historical",
                valid_to=started_at,
                snapshot_type="oci_knowledge",
            ),
            "release_snapshot": preserve_historical_snapshot(
                args.release_snapshot,
                args.release_snapshot.parent / "historical",
                valid_to=started_at,
                snapshot_type="oci_release",
            ),
        }
        rollback_sources = {
            "knowledge_index": promote_candidate(candidate_knowledge_path, args.knowledge_index, backup_dir),
            "release_snapshot": promote_candidate(candidate_release_path, args.release_snapshot, backup_dir),
        }
        promoted = True
        manifest = write_manifest(
            run_dir / "manifest.json",
            run_id=run_id,
            started_at=started_at,
            policy=policy,
            mode=args.mode,
            refresh_reason=refresh_reason,
            status="promoted",
            knowledge_index=knowledge_index,
            release_snapshot=current_release_snapshot,
            affected_source_ids=selected_source_ids,
            changed_releases=changed_releases,
            gates=gate_results,
            impact_report=impact_report,
            historical_snapshots=historical_snapshots,
            candidate_paths={
                "knowledge_index": candidate_knowledge_path,
                "release_snapshot": candidate_release_path,
            },
            promoted_paths={
                "knowledge_index": args.knowledge_index,
                "release_snapshot": args.release_snapshot,
            },
            rollback_sources=rollback_sources,
        )

    report = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "started_at": started_at,
        "policy_version": policy.get("policy_version"),
        "mode": args.mode,
        "refresh_reason": refresh_reason,
        "status": "promoted" if promoted else "no_change" if not candidate_changed else "failed_gate",
        "cadence": policy.get("cadence", {}),
        "query_time_refresh": False,
        "changed_release_count": len(changed_releases),
        "changed_releases": normalized_changed_releases or changed_releases,
        "release_intelligence": {
            "items_ingested": int(current_release_snapshot.get("release_count", len(current_release_snapshot.get("releases", [])))) if current_release_snapshot else 0,
            "items_classified": len(normalized_changed_releases),
            "impacted_services": impact_report.get("affected_services", []),
            "refresh_actions": impact_report.get("refresh_actions", []),
            "impacted_eval_cases": impact_report.get("impacted_eval_cases", {}),
            "unresolved_risks": impact_report.get("unresolved_risks", []),
        },
        "impact_report": impact_report,
        "affected_source_ids": selected_source_ids,
        "selective_reindex": bool(selected_source_ids),
        "full_reindex": refresh_reason.endswith("-forced") or args.mode == "stable-docs",
        "reindex_operations": [
            {
                "source_id": source_id,
                "operation": "selective_reindex",
                "reason": "release-impact" if normalized_changed_releases else refresh_reason,
            }
            for source_id in selected_source_ids
        ],
        "knowledge_chunk_count": knowledge_index.get("chunk_count") if knowledge_index else None,
        "oci_upload_requested": bool(args.oci_upload_bucket),
        "oci_upload_performed": upload_performed,
        "candidate_paths": {
            "knowledge_index": str(candidate_knowledge_path),
            "release_snapshot": str(candidate_release_path),
        },
        "manifest_path": str(run_dir / "manifest.json"),
        "gates": gate_results,
        "gates_passed": passed,
        "passed": passed,
        "promoted": promoted,
        "rollback_performed": False,
        "rollback_sources": {
            key: str(value) if value else None for key, value in rollback_sources.items()
        },
    }
    report["lifecycle"] = build_refresh_lifecycle(report, candidate_changed=candidate_changed)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.report_dir / "knowledge-refresh-report.json", report)
    write_json(run_dir / "knowledge-refresh-report.json", report)
    update_status_from_report(args, report, manifest, previous_status)
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
    parser.add_argument("--embedding-fallback-enabled", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal", "resource_principal"), default="config_file")
    parser.add_argument("--oci-genai-compartment-id")
    parser.add_argument("--oci-genai-embedding-model-id")
    parser.add_argument("--oci-genai-embedding-dimensions", type=int)
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
    parser.add_argument("--rollback-latest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.rollback_latest:
        report = rollback_latest(args)
        print(json.dumps(report, indent=2))
        return 0 if report["passed"] else 1
    report = execute_refresh_policy(args)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
