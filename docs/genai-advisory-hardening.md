# OCI Architecture Studio — GenAI Advisory Hardening

Date: 2026-05-15

## Goal

Harden the advisory intelligence layer so GenAI-powered responses remain grounded, citation-aware, confidence-aware, and safe for enterprise review.

The implementation is intentionally incremental:

- one codebase
- config-selected synthesis provider
- deterministic fallback
- no multi-agent orchestration
- no architecture rewrite
- eval compatibility preserved

## Active Flow

```text
prompt
-> intent classifier
-> retrieval provider
-> release snapshot check
-> synthesis provider
-> citation/evidence enforcement
-> confidence scoring
-> structured API response
-> UI confidence and evidence panels
```

## Synthesis Providers

Local and rollback-safe default:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

OCI GenAI synthesis mode:

```text
ADVISORY_SYNTHESIS_PROVIDER=oci_genai
OCI_GENAI_COMPARTMENT_ID=<compartment ocid>
OCI_GENAI_CHAT_MODEL_ID=<chat model id>
OCI_GENAI_ENDPOINT=<optional endpoint>
OCI_GENAI_MAX_TOKENS=1200
OCI_GENAI_TEMPERATURE=0.1
```

If OCI GenAI fails, the system fails closed to deterministic synthesis and records a synthesis warning. This preserves rollback and avoids serving incomplete model output.

## Prompt Construction

The GenAI prompt includes:

- user question
- optional workload context
- classified intent
- prompt template path
- intent focus
- retrieval context note
- retrieved citation chunks with IDs, titles, service metadata, stale flag, URL, and summaries

The system instruction requires:

- JSON-only output
- evidence-grounded recommendations
- no invented OCI services
- explicit uncertainty when evidence is insufficient
- no current-release impact claims without release evidence

## Citation Enforcement

After synthesis, every recommendation is passed through the advisory-quality analyzer.

The analyzer creates `evidence_links` with:

- recommendation index
- support level: `strong`, `partial`, or `unsupported`
- source chunk IDs
- source titles
- rationale

Unsupported recommendations are marked provisional. Unsupported requested service names such as `OCI Quantum Database`, `OCI Infinite DR`, `OCI AutoPilot Architect`, and `OCI Magic Migration` are flagged and suppressed from being treated as valid OCI service choices.

## Confidence Scoring

The response includes:

- retrieval confidence
- evidence confidence
- freshness confidence
- release-awareness confidence
- recommendation confidence
- overall confidence
- confidence level: `high`, `medium`, or `low`

Low-context prompts are capped to low confidence even when generic citations exist. This keeps the system from sounding certain when the user has not provided enough architecture context.

## Uncertainty Handling

The API response includes:

- `not_enough_evidence`
- `low_confidence`
- `quality_warnings`
- `unsupported_claims`
- `synthesis_warnings`
- `synthesis_fallback_used`

When evidence is weak, the response remains advisory and asks for missing workload or release context rather than presenting a final design.

## Observability

Use:

```text
GET /advisory/quality
```

Tracked fields include:

- low-confidence response count
- not-enough-evidence count
- unsupported-claim count
- stale-evidence count
- synthesis fallback count
- active/latest synthesis provider
- citation coverage
- evidence support
- recent warnings

## Evaluation Strategy

The eval runner now checks:

- synthesis response structure
- citation quality
- retrieval support
- evidence links
- confidence object shape and score bounds
- low-confidence behavior
- not-enough-evidence behavior
- unsupported service claims
- stale or unverified release guidance

Run:

```bash
app/backend/.venv/bin/python evals/run_golden.py --output-dir evals/reports/golden
app/backend/.venv/bin/python evals/run_golden.py --cases evals/edge-cases.jsonl --output-dir evals/reports/edge-cases
app/backend/.venv/bin/python evals/run_golden.py --cases evals/advisory-quality.jsonl --output-dir evals/reports/advisory-quality
```

## Rollback

Fast rollback to deterministic synthesis:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

No code fork, prompt fork, or retrieval change is required.

## Embedding Activation Readiness

Local deterministic embeddings remain the default:

```text
EMBEDDING_PROVIDER=local
```

OCI GenAI embeddings can be evaluated in a controlled path:

```text
EMBEDDING_PROVIDER=oci_genai
OCI_GENAI_COMPARTMENT_ID=<compartment ocid>
OCI_GENAI_EMBEDDING_MODEL_ID=<embedding model id>
OCI_GENAI_EMBEDDING_DIMENSIONS=<expected dimensions>
EMBEDDING_FALLBACK_ENABLED=true
```

Promotion gates:

1. `/operations/infrastructure` reports `providers.embeddings.activation_ready=true`.
2. `/retrieval/health` shows the expected embedding provider/fallback state.
3. `OCI_GENAI_EMBEDDING_DIMENSIONS` matches the generated vector length and `OCI_VECTOR_DIMENSIONS`.
4. Retrieval regression does not degrade against the local embedding baseline.
5. Oracle AI Vector Search parity is run before any active semantic retrieval promotion.

Rollback:

```text
EMBEDDING_PROVIDER=local
```

Keep `EMBEDDING_FALLBACK_ENABLED=true` during shadow validation so retrieval remains available if OCI GenAI embedding calls fail.

## Troubleshooting

If GenAI output is too generic:

1. Check retrieved citations and evidence links.
2. Add or improve source chunks for the missing OCI domain.
3. Add a failing advisory-quality eval.
4. Tighten the intent profile or synthesis instruction.

If GenAI output includes unsupported services:

1. Check `unsupported_claims`.
2. Confirm `quality_warnings` mention unsupported requested capabilities.
3. Add the pattern to the unsupported-service guardrail if it is recurring.

If release guidance overclaims:

1. Check release snapshot matches.
2. Require a release note URL or service/date.
3. Rerun release ingestion and release-aware evals.

## Next Milestone

Enable OCI GenAI synthesis in staging through configuration, run side-by-side validation against deterministic synthesis, and track quality metrics for the demo scenarios before making it the default demo path.
