# Knowledge Refresh Function

This is the OCI Functions execution target for the scheduled knowledge refresh policy.

The Terraform foundation can create:

- OCI Functions application
- knowledge refresh function
- Resource Scheduler release-note schedule
- Resource Scheduler stable-docs schedule

Build and push the function image to OCIR, then set:

```hcl
enable_knowledge_refresh_scheduler = true
knowledge_refresh_function_image   = "iad.ocir.io/<namespace>/oci-architecture-studio/knowledge-refresh:latest"
```

The function uses the same repository refresh policy:

```bash
knowledge/refresh/refresh_policy.py
```

It is invoked by OCI Resource Scheduler with a JSON body such as:

```json
{"mode":"release-watch","upload":true}
```

or:

```json
{"mode":"stable-docs","upload":true}
```

Controlled validation before enabling Resource Scheduler:

```bash
app/backend/.venv/bin/python - <<'PY'
import io
import importlib.util
import json
from pathlib import Path

function_path = Path("infra/functions/knowledge-refresh/func.py")
spec = importlib.util.spec_from_file_location("knowledge_refresh_function", function_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

payload = {
    "mode": "release-watch",
    "no_fetch": True,
    "quick_gates": True,
    "upload": False,
}
result = module.handler(None, io.BytesIO(json.dumps(payload).encode("utf-8")))
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
PY
```

This validates the Function invocation contract without fetching live documentation, uploading snapshots, promoting candidates, or enabling schedules. Keep Resource Scheduler disabled until this controlled invocation passes with the packaged image and runtime IAM policy.
