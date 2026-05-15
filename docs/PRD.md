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
- Deterministic architecture pattern profiles for common OCI advisory scenarios
- Lightweight synthesis quality scoring
- Concise architecture decision reasoning metadata for major recommendations
- Lightweight architecture consistency findings before final response return
- Confidence sub-signals for service relevance, workload alignment, migration mapping certainty, and citation coverage
- Release snapshot and temporal knowledge schemas for future release-aware architecture intelligence
- Retrieval regression and parity validation
- OCI staging deployment

## Current Working Flow

The current implementation supports a validated API/UI advisory workflow with intent classification, source-service mapping, metadata-aware retrieval, reranking, deterministic fallback synthesis, release-awareness scaffolding, and OCI staging deployment.

User flow:
1. A user asks an OCI architecture, migration, DR, cost, observability, AI/ML, security, modernization, SaaS, analytics, or release-awareness question.
2. The system classifies the prompt intent.
3. The system maps known source services to OCI service candidates when migration/source-cloud services are mentioned.
4. The system detects architecture-domain heuristics such as ecommerce, fintech, SaaS, AI/ML inference, observability, or analytics.
5. The system retrieves OCI knowledge chunks through a config-selected retrieval provider and reranks candidates using semantic score, intent match, service relevance, metadata overlap, architecture pattern match, workload/domain relevance, topic match, and migration mappings.
6. The system uses deterministic in-process orchestration metadata and a single synthesis step to produce a structured advisory response. The deterministic path applies lightweight architecture pattern profiles, retrieved services, workload/domain heuristics, citation metadata, and consistency validation.
7. Release-aware prompts are checked against point-in-time release snapshots and freshness metadata. Current release awareness is snapshot/scaffold based, not live request-time reconciliation with OCI release feeds.
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
- Deterministic synthesis uses reusable architecture profiles for HA web apps, Kubernetes modernization, fintech DR, AI inference, analytics/data lake, and multi-region SaaS.
- The response includes additive synthesis quality signals for grounding, OCI specificity, workload alignment, migration accuracy, recommendation diversity, and citation coverage.
- OCI GenAI chat synthesis adapter exists, but live GenAI use requires environment configuration and parity validation.
- If OCI GenAI synthesis fails, the system fails closed to deterministic synthesis.

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
- Backend citation metadata can associate response sections with chunk IDs, source documents, and OCI service categories.
- Decision reasoning metadata can associate major recommendations with concise rationale, tradeoffs, rejected alternatives, source chunk IDs, and confidence.
- Consistency validation can flag conflicting requirements, migration mapping coverage gaps, HA/DR alignment gaps, observability gaps, and security coverage gaps.
- Prompt templates and golden eval prompts exist in source control.
- Golden prompts route to expected intents.
- Golden evals, edge-case evals, retrieval regression, and dual-provider parity can be run locally.
- OCI staging smoke tests validate backend, frontend, retrieval, and OCI SDK access.

## Current Non-Goals / Deferred Work

- No LangGraph implementation yet.
- No advanced memory or bi-temporal storage implementation yet.
- No autonomous multi-agent execution yet.
- No always-on live LLM synthesis by default.
- No continuous live release intelligence beyond scheduled snapshot refresh and gated promotion.
- No bi-temporal retrieval; current-vs-historical temporal knowledge support is schema-oriented scaffolding only.
- Oracle AI Vector Search active reads remain guarded until schema, indexing, and query parity are validated.
- HTTPS ingress and production HA are deferred beyond the current staging slice.
