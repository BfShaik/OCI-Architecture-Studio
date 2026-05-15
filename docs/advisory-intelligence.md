# OCI Architecture Studio — Advisory Intelligence

Date: 2026-05-15

## Goal

Improve advisory quality without changing the stable deployment model or introducing uncontrolled multi-agent orchestration.

The current implementation keeps the existing flow:

```text
user prompt -> intent classifier -> retrieval -> controlled multi-agent routing -> final synthesis -> critic -> structured response
```

It adds a lightweight evidence, confidence, controlled routing, specialist contribution, aggregation, and critic layer before the response is returned.

## Current Synthesis Pipeline

1. Classify the prompt into an intent.
2. Retrieve OCI evidence through the configured retrieval provider.
3. Load the matching intent profile and prompt template.
4. Select one or more bounded specialist advisors.
5. Share the same retrieved evidence set with every selected specialist.
6. Aggregate specialist contributions into one final synthesis step.
7. Run the configured synthesis provider.
8. Link each synthesized recommendation to retrieved citations.
9. Compute confidence scores.
10. Run the validation critic over evidence, citation, freshness, unsupported-claim, and fallback signals.
11. Surface evidence gaps, unsupported requested services, stale evidence, synthesis warnings, critic findings, and missing-context warnings.
12. Return the structured advisory response to the UI.

This remains an MVP-friendly in-process pipeline. It does not add LangGraph, autonomous multi-agent planning, or a new distributed service.

Synthesis is config-selected:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic|oci_genai
```

The deterministic provider remains the rollback path. The OCI GenAI provider fails closed to deterministic synthesis if the model call fails or returns invalid JSON.

Before enabling `ADVISORY_SYNTHESIS_PROVIDER=oci_genai` in staging, run the parity checker:

```bash
app/backend/.venv/bin/python infra/scripts/genai_synthesis_parity_check.py \
  --cases evals/golden-prompts.jsonl \
  --cases evals/edge-cases.jsonl \
  --output-dir evals/reports/genai-parity
```

If OCI GenAI config is not present, the checker can be run in readiness mode:

```bash
app/backend/.venv/bin/python infra/scripts/genai_synthesis_parity_check.py \
  --cases evals/golden-prompts.jsonl \
  --output-dir evals/reports/genai-parity \
  --allow-skip
```

The checker compares deterministic and OCI GenAI outputs for intent, citation coverage, fallback usage, unsupported claims, confidence behavior, and latency.

Orchestration is also config-selected:

```text
ADVISORY_ORCHESTRATION_MODE=multi_agent_pilot|supervised|single_pass
```

`multi_agent_pilot` selects bounded specialists, records their contributions, and keeps one final synthesis step. `supervised` is the single-specialist rollback path. `single_pass` is the original advisory rollback path.

## Controlled Multi-Agent Design

The pilot agent layer is deliberately small:

- `supervisor` routes based on the already-classified intent.
- selected specialists add intent-specific focus without mutating retrieved evidence.
- `final_synthesizer` preserves single-writer final response generation through the configured synthesis provider.
- `validation_critic` reviews the final response for grounding and quality risks.

The specialist roles are:

- `architecture_advisor`
- `migration_advisor`
- `ha_dr_advisor`
- `cost_advisor`
- `release_awareness_advisor`

All roles share the same retrieval evidence, synthesis provider, citation analyzer, confidence scorer, and eval framework.

Centralized single-writer boundaries remain:

- intent classification
- retrieval provider selection
- citation linking
- confidence scoring
- final response synthesis
- quality metrics

## Citation Enforcement Design

The backend now creates `evidence_links` for each recommendation.

Each evidence link includes:

- recommendation index
- support level: `strong`, `partial`, or `unsupported`
- supporting citation chunk IDs
- supporting citation titles
- rationale

If a recommendation is not linked to retrieved evidence, the response keeps the recommendation provisional and adds an evidence-gap warning. The system does not silently present unsupported guidance as final architecture advice.

## Confidence Scoring Design

The response includes a `confidence` object:

| Score | Meaning |
|---|---|
| `retrieval` | Whether retrieval returned usable citations with source URLs and relevance. |
| `evidence` | Whether recommendations are linked to retrieved evidence. |
| `freshness` | Whether citations have acceptable freshness metadata and are not stale. |
| `release_awareness` | Whether release-sensitive prompts have matching release snapshot context. |
| `recommendation` | Combined confidence for recommendation support and citation coverage. |
| `overall` | Weighted confidence score used for the `high`, `medium`, or `low` level. |

Low-context prompts are intentionally capped to low confidence even when generic OCI chunks are retrieved. This prevents the platform from sounding certain when the user has not provided enough workload context.

## Uncertainty Handling

The response now exposes:

- `not_enough_evidence`
- `low_confidence`
- `quality_warnings`
- `unsupported_claims`

Examples:

- Ambiguous prompts such as `Make it enterprise grade on OCI` are marked as not enough evidence.
- Invented services such as `OCI AutoPilot Architect` are flagged as unsupported requested capabilities.
- Release-aware prompts remain cautious unless matching release snapshot context is available.

## Advisory Quality Observability

The backend exposes:

```text
GET /advisory/quality
```

The endpoint reports:

- request count
- low-confidence response count
- not-enough-evidence count
- unsupported-claim count
- stale-evidence count
- average citation coverage
- average evidence support
- latest confidence level
- latest orchestration mode
- latest active agents
- latest routing decision
- latest aggregation decision
- latest agent count
- critic warning count
- recent warnings

The backend also exposes:

```text
GET /orchestration/health
```

This is intentionally simple and in-process for the MVP. Production observability should later export these fields to OCI Logging, Monitoring, and dashboards.

## Evaluation Coverage

The advisory-quality suite lives at:

```text
evals/advisory-quality.jsonl
```

The orchestration-quality suite lives at:

```text
evals/orchestration-quality.jsonl
```

Run it with:

```bash
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/advisory-quality.jsonl \
  --output-dir evals/reports/advisory-quality
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/orchestration-quality.jsonl \
  --output-dir evals/reports/orchestration-quality
```

The eval runner now checks:

- response structure
- intent match
- citations
- grounding
- retrieval support
- recommendation-to-evidence links
- confidence object shape and score bounds
- low-confidence behavior
- not-enough-evidence behavior
- stale or unverified guidance
- hallucination and unsupported OCI service patterns
- controlled routing mode and required active agents
- specialist contribution count
- aggregation decision presence
- critic findings and agent trace presence

## Operational Guidance

When a response is weak:

1. Check `/retrieval/health` for active provider, chunk count, and retrieval warnings.
2. Check `/advisory/quality` for low-confidence and not-enough-evidence trends.
3. Check `/orchestration/health` for the active mode, agents, routing decision, and aggregation decision.
4. Inspect `evidence_links` to see which recommendation lacks support.
5. Inspect `agent_contributions` and `critic_findings` for evidence, citation, freshness, unsupported-claim, or specialist coverage concerns.
6. Add or improve OCI source chunks when a useful recommendation lacks evidence.
7. Tighten the intent profile when the advice is correct but too generic.
8. Add an eval case when a real prompt exposes a new failure mode.

## Current Limits

- The evidence linker is heuristic-based.
- Confidence scores are practical guardrails, not statistical probabilities.
- The corpus is still small.
- Local hashing embeddings are still active for deterministic parity.
- OCI GenAI synthesis is adapter-backed and config-gated; deterministic synthesis remains the rollback-safe default.
- The multi-agent pilot is a bounded control layer, not autonomous multi-step planning.
- Oracle AI Vector Search active reads remain guarded.

## Next Milestone

Strengthen the validation critic into a more explicit advisory policy gate:

- suppress or demote unsupported recommendations more aggressively
- require explicit release evidence for current-impact claims
- detect specialist disagreement or missing specialist coverage
- track critic outcomes in operational dashboards
- keep config-only rollback and eval compatibility intact
