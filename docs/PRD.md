# OCI Architecture Studio — Product Requirements Document

## Product Vision

OCI Architecture Studio is an AI-powered OCI architecture intelligence platform that provides grounded architecture guidance, migration advisory, cost optimization, and continuous OCI knowledge refresh.

## Current Product Capabilities

- Architecture Advisor
- Migration Advisor
- Cost Advisor
- Disaster Recovery Advisor
- Security Advisor
- Observability-oriented advisory
- AI/ML inference advisory
- SaaS-platform advisory
- Analytics-platform advisory
- Release-Aware Advisory
- AWS-to-OCI service mapping before retrieval
- Metadata-aware retrieval reranking and optional retrieval debug traces
- Section citation metadata in the backend response
- Curated 44-source local OCI knowledge corpus in the current branch
- Ingestion scaffolding for source groups, source categorization, document hierarchy, chunk lineage, release tags, metadata enrichment, and source traceability
- Corpus health validation for metadata completeness, duplicates, orphaned chunks, service tags, embeddings, and retrieval coverage gaps
- Oracle AI Vector Search provider path with schema/index tooling, vector upsert, metadata-aware similarity search, health checks, and local fallback
- OCI GenAI embedding provider path with deterministic fallback and validation diagnostics
- OCI GenAI synthesis provider path with fail-closed deterministic fallback
- Dedicated retrieval-grounded prompt builder for GenAI synthesis
- Optional synthesis debug metadata for provider, prompt sections, retrieved chunks, token estimates, and fallback reasons
- Deterministic architecture pattern profiles for common OCI advisory scenarios
- Lightweight synthesis quality scoring
- Concise architecture decision reasoning metadata for major recommendations
- Lightweight architecture consistency findings before final response return
- Confidence sub-signals for service relevance, workload alignment, migration mapping certainty, and citation coverage
- Release snapshot and temporal knowledge schemas for current-vs-historical scaffolding
- Deterministic release intelligence for release normalization, change-category classification, impacted service/source/chunk analysis, targeted eval impact detection, and refresh action recommendations
- Retrieval regression and parity validation
- OCI staging deployment

## Current Working Flow

The current implementation supports a validated API/UI advisory workflow with intent classification, source-service mapping, metadata-aware retrieval, reranking, deterministic fallback synthesis, optional OCI GenAI-assisted synthesis, snapshot-based release awareness, and OCI staging deployment.

User flow:
1. A user asks an OCI architecture, migration, DR, cost, observability, AI/ML, security, modernization, SaaS, analytics, or release-awareness question.
2. The system classifies the prompt intent.
3. The system maps known source services to OCI service candidates when migration/source-cloud services are mentioned.
4. The system detects architecture-domain heuristics such as ecommerce, fintech, SaaS, AI/ML inference, observability, or analytics.
5. The system retrieves OCI knowledge chunks through a config-selected retrieval provider and reranks candidates using semantic score, intent match, service relevance, metadata overlap, architecture pattern match, workload/domain relevance, topic match, migration mappings, and intent-critical service coverage.
6. The system uses deterministic in-process orchestration metadata and a single synthesis step to produce a structured advisory response. The deterministic path applies lightweight architecture pattern profiles, retrieved services, workload/domain heuristics, citation metadata, and consistency validation. The OCI GenAI path injects a retrieval-grounded prompt with intent, mappings, workload/domain profile, pattern hints, and retrieved chunks.
7. Release-aware prompts are checked against point-in-time release snapshots, freshness metadata, release change categories, and release impact summaries. Current release awareness is snapshot-based and deterministic; it is not live request-time reconciliation with OCI release feeds.
8. The backend returns recommendations, assumptions, risks, citations, evidence links, confidence, decision reasoning metadata, consistency findings, section citation metadata, release context, temporal knowledge context, and optional retrieval debug traces.
9. The UI displays the main advisory fields and citation cards. Full section-level citation, reasoning, consistency, and release-context UI is not implemented yet.

Current active staging retrieval:

- `oci_object_storage`

Validated rollback provider:

- `local_json`
- rollback and restore are config-only

Local development default:

- `local_json`

Supported intents:
- product overview
- architecture
- migration
- disaster recovery
- cost
- observability
- AI/ML
- security
- modernization
- SaaS platform
- analytics
- release awareness
- general

Synthesis behavior:

- Deterministic synthesis is implemented and remains the fallback-safe default unless `ADVISORY_SYNTHESIS_PROVIDER=oci_genai` is configured.
- OCI GenAI synthesis is implemented as a configurable path with deterministic fail-closed fallback.
- The GenAI prompt builder explicitly includes retrieved chunks, mapped services, workload/domain heuristics, architecture pattern hints, and response section requirements.
- Optional synthesis debug output exposes provider, model, grounding prompt sections, selected chunks, token estimates, token usage when available, and fallback reason.
- Deterministic synthesis uses reusable architecture profiles for HA web apps, Kubernetes modernization, fintech DR, AI inference, analytics/data lake, and multi-region SaaS.
- The response includes additive synthesis quality signals for grounding, OCI specificity, workload alignment, migration accuracy, recommendation diversity, and citation coverage.
- Live GenAI use requires environment configuration and parity validation.
- If OCI GenAI synthesis fails, the system fails closed to deterministic synthesis.

Embedding behavior:

- Local hashing embeddings remain the default for deterministic offline mode.
- OCI GenAI embeddings can be selected with `EMBEDDING_PROVIDER=oci_genai`.
- Embedding fallback is enabled by default through `EMBEDDING_FALLBACK_ENABLED=true`.
- The embedding path validates missing provider configuration, generation failures, and optional dimensional consistency.

Vector retrieval behavior:

- `local_json` remains the local development default.
- `oci_object_storage` remains the current staging provider until a new snapshot/provider is promoted.
- `oracle_ai_vector_search` is implemented as an optional provider that requires Oracle Database vector search configuration.
- Oracle vector retrieval supports vector similarity search, chunk upsert, metadata filtering over service/domain/pattern/workload/tag fields, and retrieval health diagnostics.
- `RETRIEVAL_FALLBACK_ENABLED=true` allows local JSON fallback if the Oracle vector provider is unavailable.
- Oracle vector promotion still requires a built index, production embedding alignment, retrieval regression, parity validation, and operational sign-off.

Corpus and ingestion behavior:

- The current local corpus is curated, not a complete OCI documentation mirror.
- The current branch contains 44 registry sources/chunks across architecture, networking, compute, containers, database, storage, edge, security, observability, cost, resilience, AI/ML, analytics, and DevOps-oriented domains.
- Ingestion supports source-group defaults, source categories, source freshness metadata, release tags, context-preserving chunking, section paths, previous/next chunk lineage, chunk content hashes, and automatic metadata enrichment.
- Corpus health checks are lightweight validation utilities; they are not autonomous crawlers or production refresh automation.

Release intelligence behavior:

- Release ingestion writes a separate release snapshot from `knowledge/release_source_registry.json`.
- Release items are normalized into deterministic change categories such as security, HA/DR, observability, cost, migration, deprecation, enhancement, and compatibility risk.
- Impact analysis maps releases to affected services, source IDs, chunk IDs, eval cases, refresh actions, and unresolved risks.
- Selective refresh can retag affected chunks with release overlay metadata and refresh embeddings/reindexing only for impacted sources.
- Historical snapshots are retained on promotion for audit/context. Retrieval remains current-first; full bi-temporal retrieval and automatic current-vs-historical answer comparison are not implemented.

Orchestration behavior:

- The current orchestration layer is deterministic and in-process.
- It exposes supervisor, specialist, and critic metadata for visibility.
- It also adds lightweight consistency findings and decision reasoning metadata.
- It does not perform autonomous planning, external tool use, persistent agent memory, raw chain-of-thought exposure, or independent agent execution.

## Acceptance Criteria

- The backend exposes `GET /health`.
- The backend exposes `POST /architecture-review`.
- The backend exposes `GET /retrieval/health`.
- The architecture review response is structured and typed.
- The frontend can submit a question and render the response.
- Retrieval, intent classification, and orchestration are separated behind service modules.
- Retrieval reranking is modular and test-covered.
- Optional retrieval debug trace is available without changing the default response behavior.
- Optional synthesis debug trace is available without changing the default response behavior.
- Backend citation metadata can associate response sections with chunk IDs, source documents, and OCI service categories.
- Decision reasoning metadata can associate major recommendations with concise rationale, tradeoffs, rejected alternatives, source chunk IDs, and confidence.
- Consistency validation can flag conflicting requirements, migration mapping coverage gaps, HA/DR alignment gaps, observability gaps, and security coverage gaps.
- Prompt templates and golden eval prompts exist in source control.
- Golden prompts route to expected intents.
- Golden evals, edge-case evals, retrieval regression, and dual-provider parity can be run locally.
- Local-vs-Oracle vector retrieval comparison cases exist for migration, SaaS, AI inference, observability, fintech DR, and analytics retrieval scenarios.
- OCI staging smoke tests validate backend, frontend, retrieval, and OCI SDK access.

## Current Non-Goals / Deferred Work

- No LangGraph implementation yet.
- No advanced memory or bi-temporal storage implementation yet.
- No autonomous multi-agent execution yet.
- No always-on live LLM synthesis by default.
- No promotion of OCI GenAI mode without parity and operational validation.
- No continuous live release intelligence beyond scheduled snapshot refresh, deterministic impact analysis, and gated promotion.
- No autonomous documentation crawling or full OCI documentation corpus yet.
- No full bi-temporal retrieval; current-vs-historical support currently consists of schemas, retained historical snapshots, temporal response metadata, and current-first retrieval with release context terms.
- Oracle AI Vector Search staging active reads remain guarded until a real index is built and query parity is validated.
- HTTPS ingress and production HA are deferred beyond the current staging slice.
