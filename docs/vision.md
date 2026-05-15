# Vision

OCI Architecture Studio helps enterprise architects, migration teams, solution engineers, and ISVs design better OCI solutions with grounded AI assistance.

The platform combines retrieval over curated OCI knowledge, deterministic advisory workflows, evaluation-driven quality checks, and release-aware synchronization so recommendations remain explainable and reviewable.

## Current State

OCI Architecture Studio now has a validated working foundation:

- React/FastAPI advisory workflow deployed in OCI staging
- intent-aware advisory profiles for product overview, architecture, migration, DR, cost, observability, AI/ML, security, modernization, SaaS platform, analytics, release-awareness, and general prompts
- metadata-aware retrieval reranking with optional debug traces
- backend section citation metadata for chunk IDs, source documents, OCI service categories, and services
- AWS-to-OCI source service mapping and domain-aware heuristics for ecommerce, fintech, SaaS, AI/ML inference, observability, and analytics scenarios
- OCI Object Storage retrieval manifest as the active staging retrieval provider
- local JSON retrieval preserved as the config-only rollback provider
- point-in-time release snapshots for release-aware guidance
- golden, edge-case, retrieval regression, and parity validation gates
- Terraform-based OCI staging slice with Object Storage, Vault, Logging, Monitoring, Events, and Notifications

The next platform milestone is to validate Oracle AI Vector Search schema, indexing, and live query parity against the active Object Storage provider before any active-read cutover.

The current orchestration layer is deterministic and in-process. Autonomous agent planning, persistent agent memory, and independent tool-using agents are future research and productization items, not current runtime behavior.

OCI GenAI synthesis is available as a configurable adapter with deterministic fail-closed fallback. Deterministic synthesis remains the safe default unless live GenAI configuration and parity validation are provided.

## Product Pillars

- Architecture guidance with clear assumptions and tradeoffs
- Migration advisory for service mapping and phased modernization
- Cost optimization guidance tied to OCI service choices
- Disaster recovery and resilience planning
- Security guidance for identity, network isolation, encryption, logging, and auditability
- Release intelligence for keeping recommendations current
- Review-ready outputs with citations, risks, and next steps
- Golden prompt regression to prevent quality drift
