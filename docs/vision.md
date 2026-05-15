# Vision

OCI Architecture Studio helps enterprise architects, migration teams, solution engineers, and ISVs design better OCI solutions with grounded AI assistance.

The platform combines retrieval over curated OCI knowledge, deterministic advisory workflows, evaluation-driven quality checks, and release-aware synchronization so recommendations remain explainable and reviewable.

## Current State

OCI Architecture Studio now has a validated working foundation:

- React/FastAPI advisory workflow deployed in OCI staging
- intent-aware advisory profiles for product overview, architecture, migration, DR, cost, observability, AI/ML, security, modernization, SaaS platform, analytics, release-awareness, and general prompts
- metadata-aware retrieval reranking with optional debug traces
- configurable OCI GenAI embeddings with deterministic fallback and validation diagnostics
- configurable OCI GenAI synthesis with retrieval-grounded prompt construction and fail-closed deterministic fallback
- optional synthesis debug traces for prompt sections, retrieved chunks, token estimates, and fallback reasons
- backend section citation metadata for chunk IDs, source documents, OCI service categories, and services
- AWS-to-OCI source service mapping and domain-aware heuristics for ecommerce, fintech, SaaS, AI/ML inference, observability, and analytics scenarios
- 44-source local OCI corpus with scalable ingestion scaffolding for source groups, source categories, chunk lineage, document hierarchy, release tags, and corpus health validation
- deterministic architecture pattern profiles, reasoning profiles, and synthesis quality signals that make fallback responses more useful while remaining explainable
- concise decision reasoning metadata, explicit tradeoff analysis, per-recommendation confidence indicators, and lightweight consistency validation for recommendation coherence
- confidence sub-signals for retrieval grounding, service relevance, workload alignment, migration mapping certainty, and citation coverage
- deterministic evaluation intelligence for advisory quality scoring, hallucination heuristics, benchmark expectation checks, provider comparison signals, and configurable quality gates
- OCI Object Storage retrieval manifest as the active staging retrieval provider
- optional Oracle AI Vector Search provider and index tooling for the next OCI-native retrieval step
- local JSON retrieval preserved as the config-only rollback provider
- point-in-time release snapshots, deterministic release impact metadata, selective refresh overlays, retained historical snapshots, and current-vs-historical schema scaffolding for release-aware guidance
- OCI-native operational diagnostics, runtime profiles, and scheduled refresh scaffolding that prefer OCI Vault, IAM, Logging, Monitoring, Notifications, Events, Resource Scheduler, Functions, Object Storage, and Oracle AI Vector Search where applicable
- golden, edge-case, advisory-quality, orchestration-quality, architecture-realism, evaluation-intelligence, retrieval regression, and parity validation gates
- Terraform-based OCI staging slice with Object Storage, Vault, Logging, Monitoring, Events, and Notifications

The next platform milestone is to keep improving advisory quality with richer official OCI corpus coverage, production-aligned embeddings/vector indexing, and stricter evaluation gates before promoting more GenAI-assisted or OCI-native retrieval behavior.

The current orchestration layer is deterministic and in-process. Autonomous agent planning, persistent agent memory, and independent tool-using agents are future research and productization items, not current runtime behavior.

OCI GenAI embeddings and synthesis are available as configurable paths with deterministic fallback. Deterministic synthesis remains the safe default unless live GenAI configuration and parity validation are provided.

The current deterministic synthesis and reasoning layer is heuristic. It improves structure, workload specificity, tradeoff visibility, grounding fidelity, and recommendation explainability, but it is not a substitute for a full OCI design review or live GenAI reasoning.

The current evaluation intelligence layer is also heuristic. It provides reproducible regression signals for architecture realism, hallucination risk, provider comparisons, and recommendation quality, but it is not an objective measure of correctness and does not use LLM-as-judge scoring.

Release-awareness is still foundational: the runtime can reference local release snapshots, classify release changes, surface impacted services/change categories, and retain historical snapshots for audit/context. It does not yet perform full automated release reconciliation or bi-temporal retrieval.

Operational hardening is intentionally OCI-centric. The current implementation exposes diagnostics and config profiles, but it is not yet a production HA runtime, does not emit custom OCI Monitoring metrics automatically, and does not require live OCI checks in local development.

The corpus remains curated rather than comprehensive. Current quality work should be read as a controlled transition from deterministic OCI advisory scaffolding toward retrieval-grounded OCI GenAI-assisted synthesis, not as a claim of full OCI documentation coverage or autonomous documentation crawling.

## Product Pillars

- Architecture guidance with clear assumptions and tradeoffs
- Migration advisory for service mapping and phased modernization
- Cost optimization guidance tied to OCI service choices
- Disaster recovery and resilience planning
- Security guidance for identity, network isolation, encryption, logging, and auditability
- Release intelligence for keeping recommendations current
- Review-ready outputs with citations, risks, and next steps
- Golden prompt regression to prevent quality drift
