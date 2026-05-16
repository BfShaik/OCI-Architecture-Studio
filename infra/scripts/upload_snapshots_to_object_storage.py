from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validate_refresh_candidate import validate_knowledge_index, validate_release_snapshot


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _object_name(base_object: str, sibling_name: str) -> str:
    if "/" not in base_object:
        return sibling_name
    prefix = base_object.rsplit("/", 1)[0]
    return f"{prefix}/{sibling_name}"


def upload_object(
    *,
    namespace: str,
    bucket: str,
    object_name: str,
    path: Path,
    auth_mode: str,
    region: str | None,
    profile: str,
) -> None:
    try:
        import oci
    except ImportError as exc:
        raise RuntimeError("OCI SDK is required for Object Storage upload.") from exc

    if auth_mode == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        client_config = {"region": region} if region else {}
        object_storage = oci.object_storage.ObjectStorageClient(client_config, signer=signer)
    elif auth_mode == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        client_config = {"region": region} if region else {}
        object_storage = oci.object_storage.ObjectStorageClient(client_config, signer=signer)
    else:
        client_config = oci.config.from_file(profile_name=profile)
        if region:
            client_config["region"] = region
        object_storage = oci.object_storage.ObjectStorageClient(client_config)

    object_storage.put_object(
        namespace_name=namespace,
        bucket_name=bucket,
        object_name=object_name,
        put_object_body=path.read_bytes(),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and upload promoted knowledge snapshots to OCI Object Storage.")
    parser.add_argument("--knowledge-index", type=Path, required=True)
    parser.add_argument("--release-snapshot", type=Path, required=True)
    parser.add_argument("--oci-auth-mode", choices=("config_file", "instance_principal", "resource_principal"), default="config_file")
    parser.add_argument("--oci-region")
    parser.add_argument("--oci-profile", default="DEFAULT")
    parser.add_argument("--oci-namespace", required=True)
    parser.add_argument("--oci-upload-bucket", required=True)
    parser.add_argument("--oci-upload-object", default="oci-rag-index.json")
    parser.add_argument("--oci-release-object")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    knowledge_index = _load_json(args.knowledge_index)
    release_snapshot = _load_json(args.release_snapshot)
    errors = [
        *validate_knowledge_index(knowledge_index, min_chunks=40),
        *validate_release_snapshot(release_snapshot, min_releases=1),
    ]
    if errors:
        print(
            json.dumps(
                {
                    "passed": False,
                    "knowledge_index": str(args.knowledge_index),
                    "release_snapshot": str(args.release_snapshot),
                    "errors": errors,
                },
                indent=2,
            )
        )
        return 1

    release_object = args.oci_release_object or _object_name(args.oci_upload_object, args.release_snapshot.name)
    upload_object(
        namespace=args.oci_namespace,
        bucket=args.oci_upload_bucket,
        object_name=args.oci_upload_object,
        path=args.knowledge_index,
        auth_mode=args.oci_auth_mode,
        region=args.oci_region,
        profile=args.oci_profile,
    )
    upload_object(
        namespace=args.oci_namespace,
        bucket=args.oci_upload_bucket,
        object_name=release_object,
        path=args.release_snapshot,
        auth_mode=args.oci_auth_mode,
        region=args.oci_region,
        profile=args.oci_profile,
    )
    summary = {
        "passed": True,
        "bucket": args.oci_upload_bucket,
        "knowledge_object": args.oci_upload_object,
        "release_object": release_object,
        "chunk_count": knowledge_index.get("chunk_count"),
        "release_count": release_snapshot.get("release_count"),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
