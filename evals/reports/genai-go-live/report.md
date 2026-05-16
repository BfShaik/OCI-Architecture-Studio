# TASK-054 GenAI Go-Live Report

Status: **Eligible for user sign-off**.

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

- OCI GenAI cases passed: `30 / 30`
- Deterministic baseline cases passed: `30 / 30`
- OCI GenAI p50 latency: `4591.54 ms`
- OCI GenAI p95 latency: `5679.36 ms`
- Deterministic p95 latency: `238.32 ms`
- p95 latency ratio vs deterministic: `23.83x`
- Estimated input tokens: `83686`
- Estimated output tokens: `15410`
- Estimated total tokens: `99096`

## Suite Results

| Suite | Passed | Total |
| --- | ---: | ---: |
| `golden` | 18 | 18 |
| `edge` | 8 | 8 |
| `genai-comparison` | 4 | 4 |

## Acceptance Gates

| Gate | Status | Evidence |
| --- | --- | --- |
| G1 Grounding | PASS | All citation-required cases returned citations and grounding prompt sections. |
| G2 No hallucinated services | PASS | No forbidden or invented service pattern was detected in the 30 GenAI responses. |
| G3 Schema compliance | PASS | All 30 GenAI responses returned HTTP 200, parsed as JSON, populated required response fields, reported `synthesis_provider=oci_genai`, and did not use fallback. |
| G4 Qualitative sign-off | PASS | 30/30 available staging cases passed after the multi-region SaaS Load Balancer coverage fix. |
| G5 Cost ceiling | REVIEW REQUIRED | Token volume was recorded, but final USD estimate should be confirmed against the tenancy billing/OCI price list before promotion. |

## Prior Failure Fix

The earlier `saas-multi-region-002` failure was addressed by strengthening the SaaS intent profile and GenAI grounding rule so multi-region SaaS ingress/failover guidance explicitly names OCI Load Balancer / Load Balancing when relevant.

## Decision

Do not auto-promote `ADVISORY_SYNTHESIS_PROVIDER=oci_genai`. The gate run is now eligible for user sign-off after final cost review.

## Rollback Readiness

Rollback remains simple because the staging default was never changed: keep `ADVISORY_SYNTHESIS_PROVIDER=deterministic`. The tested OCI GenAI model can be removed from runtime config without affecting deterministic synthesis.
