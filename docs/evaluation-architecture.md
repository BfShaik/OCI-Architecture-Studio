# OCI Architecture Studio — Evaluation Architecture

## Purpose

The evaluation foundation prevents prompt, retrieval, and orchestration regressions as OCI Architecture Studio grows from a local RAG prototype into an enterprise advisory platform.

The first production-grade eval layer should stay simple:

- structured golden prompt cases
- deterministic local runner
- score-based checks
- generated JSON and Markdown reports
- CI execution on every pull request

## Directory Structure

```text
evals/
  golden-prompts.md        Human-readable regression suite
  golden-prompts.jsonl     Machine-readable golden eval cases
  edge-cases.jsonl         Negative and stress eval cases
  run_golden.py            Local eval runner
  reports/                 Generated reports, ignored by git

docs/
  evaluation-architecture.md

.github/workflows/
  ci.yml
```

## Dataset Schema

Each JSONL record is one eval case:

```json
{
  "id": "migration-eks-rds-001",
  "prompt": "Migrate EKS + RDS to OCI.",
  "expected_intent": "migration",
  "required_services": ["EKS", "OKE", "RDS", "OCI database"],
  "required_traits": ["migration waves", "dependency mapping", "cutover"],
  "forbidden_patterns": ["guaranteed no downtime"],
  "grounding_required": true,
  "citation_required": true,
  "minimum_score": 80
}
```

Field guidance:

- `id`: stable unique case id
- `prompt`: user-facing test prompt
- `expected_intent`: expected backend intent
- `required_services`: OCI services or service mappings expected in the response
- `required_traits`: behavior, structure, or domain-specific concepts expected in the response
- `forbidden_patterns`: phrases that indicate hallucination, unsafe certainty, or bad guidance
- `grounding_required`: whether retrieved context must be present and plausible
- `citation_required`: whether response must include valid citations/chunks
- `minimum_score`: minimum passing score, 0-100

## Scoring Strategy

The MVP runner uses deterministic heuristic scoring:

| Check | Points |
|---|---:|
| Response structure | 15 |
| Intent match | 20 |
| Required services | 15 |
| Required traits | 20 |
| Citation presence | 10 |
| Grounding quality | 15 |
| Retrieval support | 10 |
| Forbidden/suspicious patterns | 10 |
| Unsupported OCI claim heuristic | 5 |
| Stale/unverified guidance | 5 |

A case passes only when:

- total score is at or above `minimum_score`
- structure passes
- intent passes
- citations pass when required
- grounding passes when required
- retrieved evidence supports required service recommendations
- no forbidden/suspicious pattern is detected
- release-aware answers avoid unverified current-release claims

This favors reliability over sophistication. When real LLM synthesis is added, the same schema can be extended with LLM-as-judge fields, but deterministic checks should remain the first gate.

## Regression Strategy

Golden prompts should be small and high-signal.

Rules:

- Add a new golden prompt only after a real failure or meaningful product gap.
- Keep prompt ids stable so reports can be compared over time.
- Do not tune the app only to pass an eval; update the eval when the product expectation changes.
- CI should block merges when golden prompt evals fail.
- CI should also run edge-case evals to catch weak grounding, generic answers, unsupported claims, and unsafe certainty.
- Store generated reports as CI artifacts, not in git.

## Hallucination And Grounding Checks

The MVP guardrails are practical heuristics:

- Missing citations fail when `citation_required` is true.
- Missing chunk ids, source URLs, or summaries fail citation validation.
- Weak relevance scores trigger grounding failures.
- Retrieval support checks compare required service claims against retrieved citation summaries.
- Forbidden phrases catch unsafe certainty, such as `guaranteed zero downtime`.
- Invented OCI service patterns catch obvious fake services.
- Release-awareness prompts must not claim latest truth without provided release context.
- Stale guidance patterns catch claims that imply live freshness without release evidence.
- Failed checks in passing cases are reported as quality warnings; failed checks in failing cases are reported as failure reasons.

Grounding does not mean every sentence is fully cited yet. The immediate goal is to prevent obviously ungrounded or stale advisory output while keeping the implementation maintainable.

## CI Integration

CI should run:

1. backend unit/API tests
2. frontend build
3. ingestion smoke test
4. golden prompt eval runner
5. edge-case eval runner

The workflow in `.github/workflows/ci.yml` performs those steps. The eval runner writes JSON and Markdown reports to `evals/reports/`; CI uploads them as artifacts.

## Retrieval Metadata Schema

Production chunks should move toward this metadata shape:

```json
{
  "chunk_id": "oci-load-balancer-overview::1",
  "source_id": "oci-load-balancer-overview",
  "source_url": "https://docs.oracle.com/...",
  "title": "OCI Load Balancer Overview",
  "service": "Load Balancer",
  "service_domain": "networking",
  "release_version": "unknown",
  "fetched_timestamp": "2026-05-14T00:00:00Z",
  "freshness_score": 0.8,
  "intent_tags": ["architecture", "dr", "cost"],
  "architecture_patterns": ["public-ingress", "high-availability"],
  "trust_level": "official",
  "source_type": "oci_service_doc"
}
```

Required production metadata:

- `source_url`
- `service`
- `service_domain`
- `release_version`
- `fetched_timestamp`
- `freshness_score`
- `intent_tags`
- `architecture_patterns`
- `trust_level`

## Rollout Plan

Phase 1:
- Add JSONL golden prompts.
- Add deterministic local eval runner.
- Add Markdown/JSON reports.
- Add CI execution.

Phase 2:
- Add richer retrieval metadata.
- Add ingestion smoke assertions for metadata completeness.
- Expand source registry for missing OCI domains.

Phase 3:
- Add citation-aware LLM synthesis.
- Add unsupported-claim checks against retrieved context.
- Add release-awareness evals with source freshness.

Phase 4:
- Add trend reports and historical comparison.
- Add production vector store and production embeddings.

## Recommended Python Libraries

Current MVP:

- `fastapi`
- `httpx`
- `pydantic`
- `pytest`
- Python standard library `json`, `re`, `argparse`, `pathlib`

Future:

- `jsonschema` for strict eval schema validation
- `rich` for local CLI output
- `beautifulsoup4` or `selectolax` for stronger HTML extraction
- `numpy` for vector math when embeddings grow

## Risk Analysis

- Keyword checks can miss semantically correct answers with different wording.
- Keyword checks can pass shallow answers that contain the right words.
- Local hash embeddings are not production semantic retrieval.
- Oracle documentation pages can include boilerplate that weakens chunks.
- Release-awareness must not imply live freshness until release ingestion exists.

Mitigation:

- Keep golden prompts small and reviewed.
- Add failure-driven evals.
- Require citations for advisory intents.
- Add freshness metadata before making current-release claims.

## Scalability Considerations

- JSONL evals scale well for the first hundreds of cases.
- The local TestClient runner avoids network/server flakiness.
- Reports can be archived as CI artifacts.
- When cases grow, split by suite: `golden`, `retrieval`, `release`, `security`.
- Keep deterministic checks as the first gate even after adding LLM-as-judge.
