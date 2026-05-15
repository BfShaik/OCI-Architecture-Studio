# OCI Architecture Studio — Advisory Intelligence

Date: 2026-05-15

## Goal

Improve advisory quality without changing the stable deployment model or introducing uncontrolled multi-agent orchestration.

The current implementation keeps the existing flow:

```text
user prompt -> intent classifier -> retrieval -> controlled multi-agent routing -> final synthesis -> critic -> structured response
```

It adds a lightweight evidence, confidence, reasoning-profile, tradeoff, controlled routing, specialist contribution, aggregation, critic, and enterprise-governance metadata layer before the response is returned.

## Current Synthesis Pipeline

1. Classify the prompt into an intent.
2. Select a deterministic architecture reasoning profile for retrieval hints and risk/tradeoff emphasis.
3. Retrieve OCI evidence through the configured retrieval provider.
4. Load the matching intent profile and prompt template.
5. Select one or more bounded specialist advisors.
6. Share the same retrieved evidence set with every selected specialist.
7. Aggregate specialist contributions into one final synthesis step.
8. Run the configured synthesis provider.
9. Link each synthesized recommendation to retrieved citations.
10. Compute confidence scores and per-recommendation confidence indicators.
11. Run deterministic tradeoff analysis for the selected reasoning profile.
12. Run the validation critic over evidence, citation, freshness, unsupported-claim, and fallback signals.
13. Build deterministic enterprise-governance metadata for executive summary, control annotations, security posture, risk classification, recommendation priority, comparison reasoning, enterprise review findings, and audit trace.
14. Build lightweight architecture topology metadata for service nodes, relationships, deployment topology, HA/DR posture, operational notes, and Mermaid flow text.
15. Surface reasoning trace, tradeoffs, governance assessment, topology summary, evidence gaps, unsupported requested services, stale evidence, synthesis warnings, critic findings, and missing-context warnings.
16. Package review-ready executive experience metadata for decision brief, implementation sequence, topology summary, comparisons, explainability highlights, and Markdown export.
16. Return the structured advisory response to the UI.

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

## Reasoning And Tradeoff Design

The backend now exposes additive reasoning metadata:

- `reasoning_trace`: selected deterministic profile, triggered heuristics, pattern hints, retrieval terms, service priorities, risk emphasis, and synthesis provider.
- `architecture_tradeoffs`: explicit decision guidance for cost/resilience, performance/complexity, managed/self-managed, latency/multi-region resilience, simplicity/scalability, and flexibility/operational-overhead tradeoffs.
- `recommendation_confidence`: per-recommendation confidence indicators with reasoning basis, supporting chunk IDs, known limitations, and assumptions.

Reasoning profiles are deterministic heuristics. They improve explainability and recommendation structure, but they do not expose raw chain-of-thought and do not perform autonomous planning.

## Enterprise Governance Metadata

The backend now exposes an additive `enterprise_governance` object in architecture-review responses.

It contains:

- `executive_summary`: business-impact framing, governance posture, risk summary, and implementation guidance.
- `governance_annotations`: per-recommendation control signals for security, resilience, FinOps, operations, migration governance, and production readiness.
- `security_posture_checks`: deterministic checks for OCI IAM, Vault/encryption, network segmentation, audit/logging, and security-zone/security-service coverage.
- `risk_classifications`: low, moderate, elevated operational, elevated security, elevated migration, and elevated cost risk signals with mitigation guidance.
- `recommendation_priorities`: recommended immediately, recommended later, optional optimizations, and advanced enterprise enhancements.
- `architecture_comparisons`: lightweight comparison reasoning such as OKE vs Compute, Autonomous Database vs Base Database, Functions vs Kubernetes, and DR topology options when relevant.
- `enterprise_review_findings`: review-oriented checks for SPOFs, weak DR posture, missing observability, IAM gaps, cost-governance gaps, and consistency findings.
- `auditability_trace`: retrieval chunk IDs, selected reasoning profile, heuristics, release influence, synthesis provider, fallback events, confidence level, and evaluation signals.

This is deterministic advisory metadata for human review. It is not an automated approval workflow, does not enforce OCI policies, and does not integrate with an external governance platform.

## Architecture Topology Metadata

The backend now exposes an additive `architecture_topology` object in architecture-review responses.

It contains:

- `nodes`: OCI service or architecture components with roles such as ingress, application runtime, data, identity, security, observability, and DR orchestration.
- `service_dependencies`: lightweight relationships between nodes, with rationale and source chunk IDs where available.
- `deployment_topology`: a short deployment-oriented summary tied to the detected intent.
- `ha_dr_topology`: a short resilience-oriented summary tied to RTO/RPO, failover, backup/restore, or provisional HA/DR needs.
- `operational_notes`: review notes for observability, IAM/Vault, migration waves, and ownership gaps.
- `mermaid_flow`: simple Mermaid text for future UI rendering.

This is intentionally not a diagram engine. It is backend topology metadata that makes advisory responses easier to review and lays groundwork for a future visualization UI.

## Executive Experience Metadata

The backend now exposes an additive `executive_experience` object in architecture-review responses.

It includes:

- `executive_summary`: concise business and risk framing for architecture review discussions.
- `decision_brief`: prioritized recommendation cards with business impact, risk visibility, and implementation priority.
- `implementation_sequence`: three lightweight phases for review, controlled implementation, and optimization.
- `architecture_visualization`: topology, deployment, HA/DR, dependency, migration-flow, and Mermaid-text summaries derived from existing topology metadata.
- `comparison_summary`: a review-friendly copy of deterministic architecture comparison reasoning.
- `explainability_highlights`: short rationale, tradeoff, confidence, and retrieval-grounding notes.
- `review_artifacts`: Markdown and structured JSON summary artifacts for lightweight export.

This is not a presentation engine and does not render live diagrams. It packages existing deterministic advisory metadata into a format that is easier for architecture review boards, platform teams, and engineering leadership to read.

## Migration And FinOps Optimization Metadata

The backend now exposes an additive `optimization_plan` object in architecture-review responses.

It includes:

- `migration_phases`: deterministic migration sequencing with discovery, coexistence/pilot, wave migration, dependency, rollback, and readiness-check guidance.
- `modernization_options`: lift-and-shift, replatforming to managed OCI services, selective refactoring, and data-platform modernization options when relevant.
- `finops_recommendations`: rightsizing, autoscaling/environment sizing, Object Storage lifecycle, GPU/inference cost control, and DR cost-tiering levers when the prompt and retrieved context support cost guidance.
- `workload_optimization_signals`: workload-specific service priorities, scaling guidance, governance weighting, and cost/performance tradeoffs for ecommerce, fintech, SaaS, analytics, AI/ML inference, and observability scenarios.
- `optimization_comparisons`: lightweight comparison reasoning for cost-optimized vs resilience-optimized design, managed vs self-managed services, serverless vs containers, and single-region vs multi-region topology where applicable.
- `implementation_readiness`: practical checks for ownership, telemetry baselines, rollout gates, rollback validation, and OCI Budgets/Cost Analysis review cadence.

The optimization layer is deterministic and heuristic. It improves migration planning, modernization framing, and FinOps review readiness, but it does not inspect live OCI billing data, call the OCI Cost Analysis APIs, or replace a formal migration factory or FinOps operating model.

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

Operational analytics also track governance policy triggers and governance risk trends from the generated advisory metadata.

The backend also exposes:

```text
GET /orchestration/health
```

Runtime readiness is exposed at:

```text
GET /operations/readiness
```

It checks startup paths, dependency configuration, API Gateway readiness, OCI DevOps readiness, runtime safeguards, fallback paths, and release-refresh state.

Runtime infrastructure visibility is exposed at:

```text
GET /operations/infrastructure
```

It reports configuration-derived OCI topology, active versus scaffolded providers, Object Storage snapshot posture, Vault/IAM posture, observability posture, scheduler and deployment workflow posture, rebuildability status, and operational gaps. It is read-only and does not replace live OCI reachability checks.

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

The architecture-realism suite lives at:

```text
evals/architecture-realism.jsonl
```

Run it with:

```bash
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/advisory-quality.jsonl \
  --output-dir evals/reports/advisory-quality
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/orchestration-quality.jsonl \
  --output-dir evals/reports/orchestration-quality
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/architecture-realism.jsonl \
  --output-dir evals/reports/architecture-realism
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/enterprise-governance.jsonl \
  --output-dir evals/reports/enterprise-governance
app/backend/.venv/bin/python evals/run_golden.py \
  --cases evals/enterprise-platform-maturity.jsonl \
  --output-dir evals/reports/enterprise-platform-maturity
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
- reasoning profile and tradeoff language in architecture-realism prompts
- deterministic architecture-quality dimensions for OCI specificity, completeness, workload alignment, migration realism, HA/DR, cost, operations, security, observability, explainability, tradeoffs, and consistency
- hallucination heuristics for invented OCI services, unsupported certainty claims, stale release claims, contradictions, and unsupported migration claims
- response-quality analytics for repetition, generic filler, OCI service frequency, pattern coverage, citation coverage, workload quality, retrieval influence, and hallucination trends

The advanced advisory quality gate is available as a local report gate:

```bash
app/backend/.venv/bin/python infra/scripts/advisory_quality_gate.py \
  --report evals/reports/evaluation-intelligence/evaluation-intelligence-report.json \
  --min-overall 0.55 \
  --min-oci-specificity 0.45 \
  --min-architecture-completeness 0.45 \
  --min-tradeoff-quality 0.35
```

These checks are deterministic heuristics intended for regression control. They are not LLM-as-judge scoring, fine-tuning feedback, or autonomous architecture approval.

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
9. Review `architecture_quality`, hallucination findings, benchmark gaps, and quality analytics in the JSON report before promoting provider or prompt changes.

## Current Limits

- The evidence linker is heuristic-based.
- Confidence scores are practical guardrails, not statistical probabilities.
- Reasoning profiles and tradeoff analysis are heuristic and bounded by retrieved corpus quality.
- The corpus is still small.
- Local hashing embeddings are still active for deterministic parity.
- OCI GenAI synthesis is adapter-backed and config-gated; deterministic synthesis remains the rollback-safe default.
- The multi-agent pilot is a bounded control layer, not autonomous multi-step planning.
- Oracle AI Vector Search active reads remain guarded.
- Evaluation intelligence scores are deterministic guardrails, not objective architecture truth.

## Next Milestone

Strengthen the validation critic into a more explicit advisory policy gate:

- suppress or demote unsupported recommendations more aggressively
- require explicit release evidence for current-impact claims
- detect specialist disagreement or missing specialist coverage
- track critic outcomes in operational dashboards
- keep config-only rollback and eval compatibility intact
