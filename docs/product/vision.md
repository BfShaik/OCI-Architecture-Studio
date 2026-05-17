# Product Vision

OCI Architecture Studio helps teams review OCI architecture decisions with grounded AI assistance. It is designed for architects, migration teams, platform engineers, solution engineers, and ISVs who need fast, explainable first-pass guidance.

## What It Is

The app turns a user question into a structured OCI architecture review with:

- recommended OCI services
- assumptions and risks
- tradeoffs and next steps
- citations and evidence links
- confidence and quality signals
- topology, governance, migration, and FinOps metadata

## Current Runtime

Staging is running the OCI-native path:

| Area | Current staging value |
| --- | --- |
| Synthesis | OCI GenAI chat, `ADVISORY_SYNTHESIS_PROVIDER=oci_genai` |
| Chat model | `xai.grok-4.3` |
| Retrieval | Oracle AI Vector Search |
| Embeddings | OCI GenAI `cohere.embed-v4.0` |
| Dimensions | `1536` |
| Vector table | `OCI_ARCHITECTURE_CHUNKS_V4` |
| Corpus | 60 curated OCI architecture chunks |

Local development can still run without OCI access by using deterministic synthesis, local JSON retrieval, and local hash embeddings.

## Product Principles

- Ground recommendations in retrieved OCI evidence.
- Keep the output structured and reviewable.
- Make citations and source links visible.
- Keep rollback paths simple and config-driven.
- Prefer OCI-native services for staging and production direction.
- Treat evals, prompts, and docs as first-class assets.

## Current Strength

The project is useful today as an internal-beta OCI architecture review assistant. It is strongest for structured first-pass reviews, migration mapping, resilience discussions, cost/operations framing, and evidence-backed architecture conversations.

## Current Limits

- The corpus is curated, not a full OCI documentation mirror.
- Release awareness uses promoted snapshots; it is not live request-time release reconciliation.
- Governance, FinOps, and quality scores are advisory metadata for human review.
- The UI has topology summaries, but not a full diagram editor.
- Production HA hardening is still future work.

## Next Product Focus

1. Add or restore team-real prompt evals.
2. Monitor live OCI GenAI quality, latency, cost, and fallback behavior.
3. Expand the OCI corpus where real team prompts expose gaps.
4. Decide whether query embedding caching is needed.
5. Prepare a production promotion checklist.
