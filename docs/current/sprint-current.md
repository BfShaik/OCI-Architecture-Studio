# Sprint Current

## Goal

Stabilize the promoted OCI GenAI + Oracle AI Vector Search staging baseline while keeping rollback simple and validation visible.

## Current Posture

- OCI GenAI synthesis is active in staging with `xai.grok-4.3`.
- OCI GenAI embeddings are active in staging with `cohere.embed-v4.0` at 1536 dimensions.
- Oracle AI Vector Search is the active retrieval provider through `OCI_ARCHITECTURE_CHUNKS_V4`.
- Object Storage and the previous 256-dimension local-hash table remain available for rollback.
- `/retrieval/health` reports a passing embedding/index guardrail and fallback inactive.

## Latest Validation

- Retrieval regression: `32/32 passed`
- Golden evals: `18/18 passed`
- Edge evals: `8/8 passed`
- Focused backend tests: `29 passed`
- Public staging health: `/health=200`, `/retrieval/health=200`
- Public architecture-review smoke: OCI GenAI synthesis, fallback disabled

## Current Priorities

1. Restore or create `evals/team-real-prompts.jsonl` and run it against live staging.
2. Watch v4 retrieval quality, latency, and fallback state during real usage.
3. Decide whether query embedding caching is needed for repeated prompts.
4. Keep runbooks and front-door docs aligned with runtime changes.

## In Scope

- OCI GenAI synthesis and embedding stabilization.
- Oracle AI Vector Search health and rollback readiness.
- Retrieval quality monitoring and eval coverage.
- Documentation cleanup that improves operator clarity.

## Out Of Scope For This Sprint

- LangGraph or autonomous agent execution.
- Advanced memory systems.
- Oracle Vector DB schema redesign beyond the promoted v4 table path.
- New embedding model experiments before v4 has real usage history.
- Production HA/runtime expansion.

## Pointers

- Current status: [status.md](status.md)
- Active plan: [living-execution-plan.md](living-execution-plan.md)
- Architecture diagrams: [architecture-diagrams.md](../architecture/architecture-diagrams.md)
- Retrieval runbook: [oci-native-retrieval-runbook.md](../runbooks/oci-native-retrieval-runbook.md)
