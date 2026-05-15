# Vision

OCI Architecture Studio helps enterprise architects, migration teams, solution engineers, and ISVs design better OCI solutions with grounded AI assistance.

The platform combines retrieval over curated OCI knowledge, structured prompt orchestration, evaluation-driven quality checks, and release-aware synchronization so recommendations remain explainable and current.

## Current State

OCI Architecture Studio now has a validated working foundation:

- React/FastAPI advisory workflow deployed in OCI staging
- intent-aware orchestration for architecture, migration, DR, cost, security, release-awareness, product overview, and general prompts
- OCI Object Storage retrieval manifest as the active staging retrieval provider
- local JSON retrieval preserved as the config-only rollback provider
- point-in-time release snapshots for release-aware guidance
- golden, edge-case, retrieval regression, and parity validation gates
- Terraform-based OCI staging slice with Object Storage, Vault, Logging, Monitoring, Events, and Notifications

The next platform milestone is to validate Oracle AI Vector Search schema, indexing, and live query parity against the active Object Storage provider before any active-read cutover.

## Product Pillars

- Architecture guidance with clear assumptions and tradeoffs
- Migration advisory for service mapping and phased modernization
- Cost optimization guidance tied to OCI service choices
- Disaster recovery and resilience planning
- Security guidance for identity, network isolation, encryption, logging, and auditability
- Release intelligence for keeping recommendations current
- Review-ready outputs with citations, risks, and next steps
- Golden prompt regression to prevent quality drift
