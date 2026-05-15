from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]


def handler(ctx, data: io.BytesIO | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if data is not None:
        raw = data.read()
        if raw:
            payload = json.loads(raw.decode("utf-8"))

    mode = str(payload.get("mode") or os.getenv("KNOWLEDGE_REFRESH_MODE") or "release-watch")
    command = [
        sys.executable,
        str(REPO_ROOT / "knowledge" / "refresh" / "refresh_policy.py"),
        "--mode",
        mode,
        "--oci-auth-mode",
        "resource_principal",
        "--report-dir",
        "/tmp/knowledge-refresh-reports",
    ]
    if payload.get("no_fetch") is True:
        command.append("--no-fetch")
    if payload.get("quick_gates") is True:
        command.append("--quick-gates")
    if payload.get("force") is True:
        command.append("--force")
    if payload.get("upload", True):
        namespace = os.getenv("OCI_OBJECT_STORAGE_NAMESPACE")
        bucket = os.getenv("SNAPSHOTS_BUCKET") or os.getenv("OCI_VECTOR_BUCKET")
        object_name = os.getenv("OCI_VECTOR_OBJECT_NAME", "oci-rag-index.json")
        if namespace and bucket:
            command.extend(
                [
                    "--oci-namespace",
                    namespace,
                    "--oci-upload-bucket",
                    bucket,
                    "--oci-upload-object",
                    object_name,
                ]
            )

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "mode": mode,
        "command": " ".join(command),
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }
