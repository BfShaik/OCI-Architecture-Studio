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
