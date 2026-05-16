# TASK-054 GenAI Go-Live Report

Status: **Do not promote yet**.

Staging was validated with a localhost-only test backend using `ADVISORY_SYNTHESIS_PROVIDER=oci_genai`. The live staging default remained `ADVISORY_SYNTHESIS_PROVIDER=deterministic` throughout the run.

## Model

- Chat model evaluated: `xai.grok-4.3`
- Embeddings were not changed in this task.
- Retrieval remained on the current staged retrieval configuration.

## Scope

- Golden prompts: `evals/golden-prompts.jsonl`
- Edge cases: `evals/edge-cases.jsonl`
- GenAI comparison prompts: `evals/genai-comparison.jsonl`
- `evals/team-real-prompts.jsonl` was not present in this repo, so the available GenAI comparison prompts were used as the team-real proxy for this run.

## Summary

- OCI GenAI cases passed: `29 / 30`
- Deterministic baseline cases passed: `30 / 30`
- OCI GenAI p50 latency: `4520.8 ms`
- OCI GenAI p95 latency: `5777.63 ms`
- Deterministic p95 latency: `210.31 ms`
- p95 latency ratio vs deterministic: `27.47x`
- Estimated input tokens: `82033`
- Estimated output tokens: `15008`
- Estimated total tokens: `97041`

## Suite Results

| Suite | Passed | Total |
| --- | ---: | ---: |
| `golden` | 17 | 18 |
| `edge` | 8 | 8 |
| `genai-comparison` | 4 | 4 |

## Acceptance Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| G1 Grounding | PASS | All citation-required cases returned citations and grounding prompt sections. |
| G2 No hallucinated services | PASS | No forbidden or invented service pattern was detected in the 30 GenAI responses. |
| G3 Schema compliance | PASS | All 30 GenAI responses returned HTTP 200, parsed as JSON, populated required response fields, reported `synthesis_provider=oci_genai`, and did not use fallback. |
| G4 Qualitative sign-off | FAIL | 29/30 cases passed. One golden case missed a required service signal. |
| G5 Cost ceiling | REVIEW REQUIRED | Token volume was recorded, but final USD estimate should be confirmed against the tenancy billing/OCI price list before promotion. |

## Blocking Failure

### `saas-multi-region-002`

- Suite: `golden`
- Expected intent: `saas_platform`
- Actual intent: `saas_platform`
- Failures: `missing required services: load balancing`
- Citations: `6`
- Synthesis quality overall: `0.905`
- Grounding quality: `1.0`
- OCI specificity: `1.0`
- Latency: `5613.86 ms`

Recommended fix: strengthen service coverage for multi-region SaaS so Load Balancer / Load Balancing is explicitly included when the prompt requires multi-region ingress or SaaS resiliency.

## Decision

Do not promote `ADVISORY_SYNTHESIS_PROVIDER=oci_genai` to staging default yet. Fix the multi-region SaaS service coverage miss, confirm the cost estimate against approved OCI billing/pricing, and rerun this report.

## Rollback Readiness

Rollback remains simple because the staging default was never changed: keep `ADVISORY_SYNTHESIS_PROVIDER=deterministic`. The tested OCI GenAI model can be removed from runtime config without affecting deterministic synthesis.
