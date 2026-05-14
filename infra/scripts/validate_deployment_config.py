from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TFVARS = {
    "tenancy_ocid",
    "parent_compartment_ocid",
    "region",
    "ssh_public_key",
    "backend_image_ocid",
    "backend_shape",
    "backend_ocpus",
    "backend_memory_gbs",
    "frontend_bucket_access_type",
    "alarm_email",
}

PLACEHOLDER_MARKERS = ("example", "REPLACE_WITH", "ocid1.image.oc1.iad.example")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OCI Architecture Studio deployment config.")
    parser.add_argument("--tfvars", required=True, help="Path to Terraform tfvars file.")
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="Allow example placeholder values. Use only for template validation.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Optional OCI CLI profile to validate in ~/.oci/config.",
    )
    return parser.parse_args()


def parse_tfvars(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"{path}:{line_number}: expected key = value")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"')
        values[key] = value
    return values


def validate_ocid(name: str, value: str, prefix: str, errors: list[str], allow_placeholders: bool) -> None:
    if allow_placeholders and "example" in value:
        return
    if not value.startswith(prefix):
        errors.append(f"{name} must start with {prefix}")


def validate(values: dict[str, str], allow_placeholders: bool) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TFVARS - values.keys())
    if missing:
        errors.append(f"missing required keys: {', '.join(missing)}")

    for key in sorted(REQUIRED_TFVARS & values.keys()):
        value = values[key]
        if not value:
            errors.append(f"{key} must not be empty")
        if not allow_placeholders and any(marker in value for marker in PLACEHOLDER_MARKERS):
            errors.append(f"{key} still contains a placeholder value")

    if "tenancy_ocid" in values:
        validate_ocid("tenancy_ocid", values["tenancy_ocid"], "ocid1.tenancy.", errors, allow_placeholders)
    if "parent_compartment_ocid" in values:
        validate_ocid(
            "parent_compartment_ocid",
            values["parent_compartment_ocid"],
            "ocid1.compartment.",
            errors,
            allow_placeholders,
        )
    if "backend_image_ocid" in values:
        validate_ocid("backend_image_ocid", values["backend_image_ocid"], "ocid1.image.", errors, allow_placeholders)

    if "region" in values and not re.fullmatch(r"[a-z]+-[a-z]+-\d", values["region"]):
        errors.append("region should look like us-ashburn-1")
    if "alarm_email" in values and "@" not in values["alarm_email"]:
        errors.append("alarm_email must be an email address")
    if "ssh_public_key" in values and not values["ssh_public_key"].startswith(("ssh-rsa ", "ssh-ed25519 ")):
        errors.append("ssh_public_key must start with ssh-rsa or ssh-ed25519")

    for numeric_key in ("backend_ocpus", "backend_memory_gbs"):
        if numeric_key in values:
            try:
                numeric_value = float(values[numeric_key])
            except ValueError:
                errors.append(f"{numeric_key} must be numeric")
            else:
                if numeric_value <= 0:
                    errors.append(f"{numeric_key} must be greater than 0")

    return errors


def validate_profile(profile: str) -> list[str]:
    try:
        import oci
    except ImportError:
        return ["OCI SDK is not installed; install infra/requirements.txt to validate OCI profile"]

    try:
        config = oci.config.from_file(profile_name=profile)
        oci.config.validate_config(config)
    except Exception as exc:  # noqa: BLE001 - report any config failure as a validation error.
        return [f"OCI profile {profile} is not valid: {exc}"]
    return []


def main() -> int:
    args = parse_args()
    path = Path(args.tfvars)
    if not path.exists():
        print(f"FAIL tfvars file not found: {path}", file=sys.stderr)
        return 1

    try:
        values = parse_tfvars(path)
    except ValueError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    errors = validate(values, args.allow_placeholders)
    if args.profile:
        errors.extend(validate_profile(args.profile))

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1

    print(f"PASS deployment config: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
