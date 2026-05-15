from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only readiness check for the OCI Object Storage Terraform backend."
    )
    parser.add_argument(
        "--terraform-root",
        default="infra/terraform",
        help="Path to the Terraform root that contains backend.object-storage.example.tf.",
    )
    parser.add_argument(
        "--env",
        default="staging",
        choices=("dev", "test", "staging"),
        help="Terraform environment directory to inspect.",
    )
    parser.add_argument("--profile", default="DEFAULT", help="OCI CLI profile for live Object Storage validation.")
    parser.add_argument("--namespace", help="Expected OCI Object Storage namespace.")
    parser.add_argument("--bucket-name", help="Expected Terraform state Object Storage bucket name.")
    parser.add_argument("--region", help="Expected OCI region for the backend.")
    parser.add_argument(
        "--skip-oci",
        action="store_true",
        help="Skip live OCI SDK checks and only inspect local Terraform files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON report.")
    return parser.parse_args()


def result(name: str, status: str, message: str) -> CheckResult:
    return CheckResult(name=name, status=status, message=message)


def check_local_files(terraform_root: Path, env: str) -> list[CheckResult]:
    checks: list[CheckResult] = []
    template = terraform_root / "backend.object-storage.example.tf"
    env_dir = terraform_root / "envs" / env
    backend_tf = env_dir / "backend.tf"
    local_state = env_dir / "terraform.tfstate"

    if template.exists():
        checks.append(result("backend_template", "pass", f"Found backend template: {template}"))
    else:
        checks.append(result("backend_template", "fail", f"Missing backend template: {template}"))

    if env_dir.exists():
        checks.append(result("environment_directory", "pass", f"Found Terraform environment: {env_dir}"))
    else:
        checks.append(result("environment_directory", "fail", f"Missing Terraform environment: {env_dir}"))

    if backend_tf.exists():
        checks.append(result("environment_backend", "pass", f"Environment backend.tf exists: {backend_tf}"))
    else:
        checks.append(
            result(
                "environment_backend",
                "warn",
                f"No backend.tf found for {env}; remote state is not configured for this environment.",
            )
        )

    if local_state.exists():
        checks.append(
            result(
                "local_state",
                "warn",
                f"Local terraform.tfstate exists at {local_state}; review before any manual state migration.",
            )
        )
    else:
        checks.append(result("local_state", "pass", f"No local terraform.tfstate found at {local_state}"))

    return checks


def check_oci_access(
    *,
    profile: str,
    expected_namespace: str | None,
    bucket_name: str | None,
    expected_region: str | None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    try:
        import oci
    except ImportError:
        return [
            result(
                "oci_sdk",
                "fail",
                "OCI SDK is not installed. Install infra/requirements.txt to run live Object Storage checks.",
            )
        ]

    try:
        config = oci.config.from_file(profile_name=profile)
        oci.config.validate_config(config)
    except Exception as exc:  # noqa: BLE001 - surface any local OCI profile/config problem.
        return [result("oci_profile", "fail", f"OCI profile {profile} is not usable: {exc}")]

    region = config.get("region")
    if expected_region and region != expected_region:
        checks.append(result("oci_region", "fail", f"Profile region is {region}; expected {expected_region}."))
    else:
        checks.append(result("oci_region", "pass", f"Profile region: {region}"))

    try:
        object_storage = oci.object_storage.ObjectStorageClient(config)
        namespace = object_storage.get_namespace().data
    except Exception as exc:  # noqa: BLE001 - report Object Storage access failures directly.
        return checks + [result("object_storage_namespace", "fail", f"Could not read Object Storage namespace: {exc}")]

    if expected_namespace and namespace != expected_namespace:
        checks.append(
            result(
                "object_storage_namespace",
                "fail",
                f"Object Storage namespace is {namespace}; expected {expected_namespace}.",
            )
        )
    else:
        checks.append(result("object_storage_namespace", "pass", f"Object Storage namespace: {namespace}"))

    if bucket_name:
        try:
            bucket = object_storage.get_bucket(namespace, bucket_name).data
        except Exception as exc:  # noqa: BLE001 - report bucket lookup failure directly.
            checks.append(result("state_bucket", "fail", f"State bucket {bucket_name} is not readable: {exc}"))
        else:
            checks.append(result("state_bucket", "pass", f"State bucket readable: {bucket.name}"))
    else:
        checks.append(result("state_bucket", "warn", "No --bucket-name provided; skipped state bucket lookup."))

    return checks


def summarize(checks: list[CheckResult]) -> dict[str, Any]:
    return {
        "status": "fail" if any(check.status == "fail" for check in checks) else "pass",
        "checks": [asdict(check) for check in checks],
    }


def print_text_report(report: dict[str, Any]) -> None:
    for check in report["checks"]:
        print(f"{check['status'].upper()} {check['name']}: {check['message']}")
    print(f"SUMMARY {report['status'].upper()}")


def main() -> int:
    args = parse_args()
    terraform_root = Path(args.terraform_root)

    checks = check_local_files(terraform_root, args.env)
    if args.skip_oci:
        checks.append(result("oci_live_checks", "warn", "Skipped live OCI Object Storage checks."))
    else:
        checks.extend(
            check_oci_access(
                profile=args.profile,
                expected_namespace=args.namespace,
                bucket_name=args.bucket_name,
                expected_region=args.region,
            )
        )

    report = summarize(checks)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
