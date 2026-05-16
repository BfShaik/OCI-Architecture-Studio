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
- Curated 47-chunk OCI knowledge corpus in the current branch
- Ingestion scaffolding for source groups, source categorization, document hierarchy, chunk lineage, release tags, metadata enrichment, and source traceability
- Corpus health validation for metadata completeness, duplicates, orphaned chunks, service tags, embeddings, and retrieval coverage gaps
- Oracle AI Vector Search provider path with schema/index tooling, vector upsert, metadata-aware similarity search, health checks, and local fallback
- OCI GenAI embedding provider path with deterministic fallback and validation diagnostics
- OCI GenAI synthesis provider path with fail-closed deterministic fallback
- Dedicated retrieval-grounded prompt builder for GenAI synthesis
- Optional synthesis debug metadata for provider, prompt sections, retrieved chunks, token estimates, and fallback reasons
- Deterministic architecture pattern profiles for common OCI advisory scenarios
- Deterministic architecture reasoning profiles for HA/DR, migration, SaaS, fintech, AI/ML inference, analytics/data, observability, and cost-optimized workloads
- Lightweight synthesis quality scoring
- Deterministic evaluation intelligence for architecture realism, OCI specificity, hallucination risk, recommendation explainability, tradeoff quality, and regression gating
- Concise architecture decision reasoning metadata for major recommendations
- Explicit architecture tradeoff analysis and per-recommendation confidence indicators
- Lightweight architecture consistency findings before final response return
- Deterministic enterprise governance assessment metadata with executive summary, policy annotations, OCI security posture checks, risk classification, recommendation prioritization, comparison reasoning, enterprise review findings, and auditability trace
- Lightweight architecture topology metadata with service nodes, dependency relationships, deployment topology, HA/DR topology, operational notes, and Mermaid flow text for future UI visualization
- Executive experience metadata with review-ready summary, decision brief, implementation sequence, topology visualization summary, comparison summary, explainability highlights, and Markdown export artifact
- Deterministic migration and FinOps optimization metadata with phased migration sequencing, modernization options, FinOps levers, workload optimization signals, optimization comparisons, and implementation readiness checks
- Confidence sub-signals for service relevance, workload alignment, migration mapping certainty, and citation coverage
- Release snapshot and temporal knowledge schemas for current-vs-historical scaffolding
- Deterministic release intelligence for release normalization, change-category classification, impacted service/source/chunk analysis, targeted eval impact detection, and refresh action recommendations
- OCI-native operational diagnostics for deployment profiles, retrieval/vector health, release freshness, synthesis provider availability, secret/config posture, observability configuration, infrastructure visibility, rebuildability gaps, and runtime analytics
- Runtime profile examples for local development, OCI VM, and OKE
- Retrieval regression and parity validation
- OCI staging deployment

## Current Working Flow

The current implementation supports a validated API/UI advisory workflow with intent classification, source-service mapping, metadata-aware retrieval, reranking, deterministic fallback synthesis, optional OCI GenAI-assisted synthesis, snapshot-based release awareness, and OCI staging deployment.

User flow:
1. A user asks an OCI architecture, migration, DR, cost, observability, AI/ML, security, modernization, SaaS, analytics, or release-awareness question.
2. The system classifies the prompt intent.
3. The system maps known source services to OCI service candidates when migration/source-cloud services are mentioned.
4. The system detects architecture-domain heuristics such as ecommerce, fintech, SaaS, AI/ML inference, observability, or analytics.
5. The system selects a deterministic reasoning profile and uses its retrieval terms, service priorities, architecture patterns, workload hints, and risk emphasis to bias retrieval while preserving the same retrieval provider interface.
6. The system retrieves OCI knowledge chunks through a config-selected retrieval provider and reranks candidates using semantic score, intent match, service relevance, metadata overlap, architecture pattern match, workload/domain relevance, topic match, migration mappings, reasoning-profile hints, and intent-critical service coverage.
7. The system uses deterministic in-process orchestration metadata and a single synthesis step to produce a structured advisory response. The deterministic path applies lightweight architecture pattern profiles, reasoning profiles, retrieved services, workload/domain heuristics, citation metadata, tradeoff analysis, and consistency validation. The OCI GenAI path injects a retrieval-grounded prompt with intent, mappings, workload/domain profile, pattern hints, reasoning profile, and retrieved chunks.
8. Release-aware prompts are checked against point-in-time release snapshots, freshness metadata, release change categories, and release impact summaries. Current release awareness is snapshot-based and deterministic; it is not live request-time reconciliation with OCI release feeds.
9. The backend returns recommendations, assumptions, risks, citations, evidence links, confidence, reasoning trace metadata, tradeoff analysis, per-recommendation confidence, decision reasoning metadata, consistency findings, deterministic enterprise-governance metadata, architecture topology metadata, executive experience metadata, migration/FinOps optimization metadata, section citation metadata, release context, temporal knowledge context, and optional retrieval debug traces.
10. The UI displays the main advisory fields, executive brief, implementation sequence, lightweight topology/dependency summaries, decision comparisons, explainability highlights, migration/FinOps optimization summaries, citation cards, and a Markdown export action. Full section-level citation UI, live diagram rendering, and release-context UI are not implemented yet.

Operational flow:

- Runtime mode is selected by `DEPLOYMENT_PROFILE=local_dev|oci_vm|oke`.
- Local development keeps deterministic local retrieval/synthesis and does not require OCI connectivity.
- OCI VM and OKE profiles prefer OCI IAM-based runtime identity, OCI Vault for sensitive configuration, OCI Object Storage or Oracle AI Vector Search for retrieval, and OCI Logging/Monitoring/Notifications for operations.
- The current staging scheduled refresh path runs from backend OCI Compute VM cron. Release-watch uses live fetch, quick gates, gated promotion, and Object Storage upload; stable-doc refresh remains safe/candidate-only.
- `/operations/profile`, `/operations/health`, `/operations/readiness`, `/operations/infrastructure`, and `/operations/analytics` expose additive diagnostics without changing the architecture-review API.
- Operational analytics include deterministic governance policy-trigger and risk-trend counters from generated advisory metadata.
- Runtime readiness diagnostics check startup paths, dependency configuration, API Gateway readiness, OCI DevOps readiness, runtime safeguards, fallback paths, and release-refresh state.
- Infrastructure visibility diagnostics report the configured OCI runtime topology, API exposure mode, retrieval/synthesis/embedding providers, Object Storage snapshot posture, Vault/IAM posture, observability posture, scheduler/deployment workflow posture, and configuration-derived rebuildability gaps. This endpoint is read-only and does not prove live OCI resource reachability unless connectivity checks are enabled.
- The internal beta readiness gate validates deployed endpoints, retrieval health, operational diagnostics, governance/executive/topology metadata, migration/FinOps optimization metadata, release/temporal metadata, citations, and accepted staging warnings.
- Live OCI SDK connectivity checks are disabled by default and should be enabled only after IAM policies and Vault access are ready.

Evaluation flow:

- Golden, edge-case, advisory-quality, orchestration-quality, architecture-realism, evaluation-intelligence, enterprise-governance, enterprise-platform-maturity, and runtime-production-readiness datasets can be run locally through the deterministic eval runner.
- Enterprise-governance and enterprise-platform-maturity evals measure governance annotations, auditability, risk classification, topology/explainability, migration governance, security realism, operational realism, runtime degradation handling, executive usability, and FinOps signals.
- Executive-experience evals measure executive-summary quality, presentation-oriented sequencing, comparison usefulness, visualization usefulness, operational-readiness clarity, and export-friendly report content.
- FinOps-migration optimization evals measure phased sequencing, coexistence/rollback realism, modernization guidance, rightsizing/autoscaling/storage lifecycle recommendations, workload-specific optimization signals, cost-performance tradeoffs, and implementation readiness.
- The evaluation-intelligence layer scores generated responses across OCI specificity, completeness, workload alignment, migration realism, HA/DR, cost, operations, security, observability, explainability, tradeoff quality, and consistency.
- Hallucination heuristics flag invented OCI services, unsupported certainty claims, stale release claims, contradictory recommendations, and unsupported migration claims.
- Provider comparison tooling can compare deterministic synthesis with OCI GenAI synthesis when live OCI GenAI configuration is available; without those settings it runs in skip-safe readiness mode.
- The scoring layer is a regression guardrail, not an autonomous judge, fine-tuning loop, or substitute for OCI expert review.

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
- Deterministic reasoning profiles add profile-specific retrieval hints, service priorities, risk emphasis, tradeoff dimensions, and recommendation guidance before final synthesis.
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
- Oracle vector shadow infrastructure, schema/index, and sync are implemented and validated against the refreshed 47-chunk snapshot. Active-read promotion still requires refreshed parity, retrieval regression, staging smoke, rollback validation, production embedding alignment, and operational sign-off.

Corpus and ingestion behavior:

- The current local corpus is curated, not a complete OCI documentation mirror.
- The current branch contains 47 chunks across architecture, networking, compute, containers, database, storage, edge, security, observability, cost, resilience, AI/ML, analytics, and DevOps-oriented domains.
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
- It also adds lightweight reasoning profile metadata, tradeoff analysis, per-recommendation confidence indicators, consistency findings, and decision reasoning metadata.
- Reasoning profiles are explainable heuristics, not hidden chain-of-thought or autonomous planner state.
- It does not perform autonomous planning, external tool use, persistent agent memory, raw chain-of-thought exposure, or independent agent execution.

FinOps and migration optimization behavior:

- The optimization layer is deterministic and additive. It builds `optimization_plan` metadata after synthesis and before final advisory quality scoring.
- Migration and modernization prompts can receive phased migration plans, coexistence/pilot guidance, rollback considerations, dependency sequencing, and modernization options such as lift-and-shift, replatforming to managed OCI services, and selective refactoring.
- Cost-oriented prompts can receive rightsizing, autoscaling, environment sizing, storage lifecycle, GPU/inference, and DR cost-tiering guidance.
- Workload optimization signals are heuristic and currently cover ecommerce, fintech, SaaS, analytics, AI/ML inference, and observability patterns.
- OCI Budgets and Cost Analysis are referenced as recommended OCI-native operating controls. The current implementation does not call live OCI Cost Analysis APIs or calculate tenancy spend from billing data.

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
- Reasoning trace metadata can show the selected reasoning profile, triggered heuristics, pattern hints, retrieval terms, service priorities, risk emphasis, and synthesis provider.
- Architecture tradeoff metadata can show explicit decision guidance for cost/resilience, performance/complexity, managed/self-managed, latency/resilience, simplicity/scalability, and flexibility/overhead dimensions.
- Consistency validation can flag conflicting requirements, migration mapping coverage gaps, HA/DR alignment gaps, observability gaps, and security coverage gaps.
- Enterprise governance assessment can classify recommendation risks, annotate policy/control implications, prioritize recommendations, provide comparison reasoning, and preserve an auditability trace from retrieval sources through synthesis provider and confidence signals.
- Architecture topology metadata can summarize service relationships, deployment topology, HA/DR posture, and operational dependencies for future diagram rendering.
- Executive experience metadata can package advisory output into decision briefs, phased implementation guidance, topology summaries, comparison summaries, explainability highlights, and Markdown review artifacts.
- Architecture quality scoring can report deterministic dimension scores, benchmark expectation matches, hallucination findings, response-quality analytics, and configurable advisory quality-gate failures.
- Prompt templates and golden eval prompts exist in source control.
- Golden prompts route to expected intents.
- Golden evals, edge-case evals, retrieval regression, and dual-provider parity can be run locally.
- Local-vs-Oracle vector retrieval comparison cases exist for migration, SaaS, AI inference, observability, fintech DR, and analytics retrieval scenarios.
- OCI staging smoke tests validate backend, frontend, retrieval, and OCI SDK access.
- Operational readiness checks validate health endpoints, retrieval availability, deployment profile, operational diagnostics, and analytics visibility.
- Runtime readiness checks validate operational safeguards and provider configuration without requiring live OCI checks in local development.

## Current Non-Goals / Deferred Work

- No LangGraph implementation yet.
- No advanced memory or bi-temporal storage implementation yet.
- No autonomous multi-agent execution yet.
- No architecture reasoning engine based on hidden chain-of-thought, self-planning, or autonomous tool use.
- No automated policy enforcement, approval workflow, or external governance platform integration in the enterprise governance layer; it is deterministic advisory metadata for human review.
- No complex diagram engine or frontend Mermaid renderer yet; current visualization support is backend topology metadata, dependency summaries, and lightweight frontend cards.
- No LLM-as-judge scoring, model fine-tuning, or autonomous evaluation agent in the current evaluation intelligence layer.
- No always-on live LLM synthesis by default.
- No promotion of OCI GenAI mode without parity and operational validation.
- No request-time live release intelligence beyond scheduled snapshot refresh, deterministic impact analysis, and gated promotion.
- No external scheduler or operational workflow platform; current scheduled refresh uses cron on the OCI backend VM.
- No mandatory live OCI connectivity checks in local development.
- No autonomous documentation crawling or full OCI documentation corpus yet.
- No full bi-temporal retrieval; current-vs-historical support currently consists of schemas, retained historical snapshots, temporal response metadata, and current-first retrieval with release context terms.
- Oracle AI Vector Search staging active reads remain guarded even though the shadow table/index exists; promotion waits for refreshed parity, regression, smoke, rollback, and operational approval gates.
- HTTPS ingress and production HA are deferred beyond the current staging slice.
