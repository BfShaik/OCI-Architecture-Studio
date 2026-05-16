# Knowledge Refresh Function

This is the OCI Functions execution target for the scheduled knowledge refresh policy.

Current staging decision: this path is **deferred**. The image was built and pushed with an immutable OCIR tag, and local/container candidate validation passed, but the deployed OCI Function invocation failed before handler execution with `FunctionInvokeContainerInitFail`. Staging refresh now runs from cron on the backend OCI Compute VM while this Function image startup issue is repaired.

The Terraform foundation can create:

- OCI Functions application
- knowledge refresh function
- Resource Scheduler release-note schedule
- Resource Scheduler stable-docs schedule

After the packaged invocation issue is fixed, build and push the function image to OCIR, then set:

```hcl
enable_knowledge_refresh_scheduler = true
knowledge_refresh_function_image   = "iad.ocir.io/<namespace>/oci-architecture-studio/knowledge-refresh:<immutable-tag>"
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
    "candidate_only": True,
    "upload": False,
}
result = module.handler(None, io.BytesIO(json.dumps(payload).encode("utf-8")))
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
PY
```

This validates the Function invocation contract without fetching live documentation, uploading snapshots, promoting candidates, or enabling schedules. Keep Resource Scheduler disabled until this controlled invocation passes with the packaged image and runtime IAM policy.

## Current VM Cron Alternative

The active staging refresh scheduler is documented in:

- `infra/scripts/run_knowledge_refresh_vm.sh`
- `infra/scripts/install_knowledge_refresh_vm_cron.sh`
- `docs/continuous-intelligence-operations.md`

Current staging posture:

- release-watch: live fetch, quick gates, gated promotion, Object Storage upload
- stable-docs: no-fetch, quick gates, candidate-only, no upload

This still runs inside OCI, uses the same Python refresh policy, and avoids GitHub Actions or external schedulers.

## Resource Scheduler Enablement

Current decision: keep schedules disabled until the Function image is rebuilt, pushed to OCIR, and validated through a controlled packaged invocation.

Prerequisites:

- Function image exists in OCIR and is referenced by `knowledge_refresh_function_image`.
- The controlled Function invocation passes with the packaged image.
- Terraform plan shows only the expected OCI Functions application, Function, Resource Scheduler schedules, dynamic group, and policy changes.
- Runtime diagnostics expose `OCI_KNOWLEDGE_REFRESH_FUNCTION_OCID`, `OCI_KNOWLEDGE_REFRESH_RELEASE_SCHEDULE_OCID`, and/or `OCI_KNOWLEDGE_REFRESH_STABLE_DOCS_SCHEDULE_OCID` after apply.

Enable in local `terraform.tfvars`:

```hcl
enable_knowledge_refresh_scheduler         = true
knowledge_refresh_function_image           = "iad.ocir.io/<namespace>/oci-architecture-studio/knowledge-refresh:<tag>"
knowledge_refresh_release_cron             = "17 */6 * * *"
knowledge_refresh_stable_docs_cron         = "23 2 * * 0"
knowledge_refresh_function_memory_mbs      = 1024
knowledge_refresh_function_timeout_seconds = 300
```

Validation:

```bash
terraform -chdir=infra/terraform/envs/staging validate
terraform -chdir=infra/terraform/envs/staging plan
python3 infra/scripts/operational_readiness_check.py \
  --api-base-url http://<backend-public-ip>:8000 \
  --require-oci-profile
```

Rollback:

1. Set `enable_knowledge_refresh_scheduler = false`.
2. Run `terraform plan` and verify only scheduler/function resources are removed or disabled.
3. Apply only after manual refresh remains available.
4. Confirm diagnostics report the scheduler as scaffolded but inactive.
