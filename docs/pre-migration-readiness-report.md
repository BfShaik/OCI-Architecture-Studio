# OCI Architecture Studio — Pre-Migration Readiness Report

Date: 2026-05-14

## Scope

This report validates the current OCI Architecture Studio platform before OCI-native retrieval migration begins.

The review intentionally does not redesign retrieval. It checks whether the existing local RAG, eval, release-awareness, deployment, and CI/CD foundations are stable enough to introduce an OCI-native retrieval adapter behind the same application flow.

## Overall Assessment

Decision: **Go for incremental OCI-native retrieval migration**

Confidence:

- Platform stability: **High**
- Current retrieval quality: **Medium**
- Release-awareness maturity: **Medium-low**
- Deployment readiness: **Medium**

The system is stable enough to begin OCI-native retrieval migration if the current JSON vector store remains the default local fallback and the new OCI-native path is introduced behind configuration.

## Validation Summary

| Check | Result | Timing | Notes |
|---|---:|---:|---|
| Knowledge ingestion smoke | Passed | 0.50s | Generated 13 knowledge chunks |
| Release ingestion smoke | Passed | 0.48s | Generated 3 release items |
| Backend tests | Passed | 3.48s | 22 tests passed |
| Backend tests repeat | Passed | 5.55s | Flake check passed |
| Golden evals | Passed | 2.34s | 6 of 6 passed |
| Golden evals repeat | Passed | 3.46s | Flake check passed |
| Edge-case evals | Passed | 2.45s | 8 of 8 passed |
| Frontend build | Passed | 15.20s | Vite build completed |
| Deployment config validation | Passed | 2.58s | Staging tfvars/config passed validation |
| Terraform staging validate | Passed | 3.14s | Terraform configuration valid |
| OCI access check | Passed | 3.02s | Object Storage namespace: `idsmrn7rvqb6` |
| Terraform staging plan | Passed | 4.63s | 19 to add, 0 to change, 0 to destroy |
| Local API smoke | Passed | Not timed | Architecture and release-aware citation paths passed |

## Flaky-Test Detection

No flakiness was observed in the repeated checks.

Repeated runs:

- Backend tests: passed twice
- Golden evals: passed twice

Recommendation: keep repeating backend tests and golden evals during retrieval adapter work because those are the fastest signal for regression.

## Retrieval Quality Assessment

Current retrieval implementation:

- Uses deterministic local hashing embeddings.
- Uses a local JSON vector index.
- Filters and ranks with intent-aware retrieval.
- Returns citation-ready `RetrievedSource` records.
- Includes freshness and trust metadata.

Current index inspection:

- Knowledge chunks: 13
- Sources represented: 13
- Missing required metadata counts:
  - `source_url`: 0
  - `service`: 0
  - `service_domain`: 0
  - `intent_tags`: 0
  - `fetched_timestamp`: 0
  - `freshness_score`: 0
  - `trust_level`: 0

Represented services and source areas:

- Architecture Center
- Well-Architected Framework
- Virtual Cloud Network
- Load Balancer
- Object Storage
- CDN
- Compute
- Database Services
- OCI Kubernetes Engine
- Database Migration
- Full Stack Disaster Recovery
- Cost Management
- Security Services

Strengths:

- Retrieval consistently returns official OCI-oriented sources.
- Citations include service, domain, freshness, trust level, URL, score, and snippets.
- Intent-aware retrieval improves relevance for migration, DR, and cost scenarios.
- The eval runner checks citation presence, grounding, stale guidance, and unsupported claims.

Weaknesses:

- The corpus is intentionally small and cannot support broad production OCI advisory coverage.
- Hash embeddings validate flow but are not production semantic retrieval.
- Source freshness is metadata-driven and coarse.
- Release awareness uses a small local release snapshot rather than live release intelligence.
- The backend response is still profile/template-driven, not full citation-aware LLM synthesis.

## Architecture Scenario Spot Checks

### Architecture Design

Prompt: `Design a highly available ecommerce platform on OCI.`

Intent result: `architecture`

Retrieved evidence:

- OCI Database Services Overview
- OCI Object Storage Overview
- OCI Architecture Center
- OCI Load Balancer Overview
- OCI CDN Overview
- OCI Compute Overview

Quality assessment:

- Good support for multi-tier ecommerce design, load balancing, compute, database tier, static assets, and CDN.
- Response includes ecommerce-specific risks such as checkout consistency, payment isolation, peak-sale scaling, and fraud controls.
- Weak area: corpus does not yet include dedicated WAF, DNS, IAM, Observability, or streaming/eventing sources.

### Migration

Prompt: `Migrate EKS + RDS to OCI.`

Intent result: `migration`

Retrieved evidence:

- OCI Kubernetes Engine Overview
- OCI Database Migration Overview
- OCI Database Services Overview
- OCI Load Balancer Overview
- OCI Cost Management Overview
- OCI CDN Overview

Quality assessment:

- Correctly maps EKS to OKE.
- Correctly maps RDS to OCI database target options after engine/version discovery.
- Includes migration waves, networking, IAM, DNS, secrets, rollback, replication, and validation.
- Weak area: needs richer source coverage for container registry, IAM mapping, DNS, network connectivity, and engine-specific database migration paths.

### HA/DR

Prompt: `Recommend OCI services for fintech DR.`

Intent result: `dr`

Retrieved evidence:

- OCI Full Stack Disaster Recovery Overview
- OCI Database Services Overview
- OCI Virtual Cloud Network Overview
- OCI Security Services Overview
- OCI Well-Architected Framework
- OCI Database Migration Overview

Quality assessment:

- Strong DR focus with RTO/RPO, cross-region topology, backups, replication, failover, Vault, logging, monitoring, auditability, and runbooks.
- Correctly avoids generic architecture-only recommendations.
- Weak area: needs dedicated DNS/traffic steering and per-database replication source coverage.

### Cost Optimization

Prompt: `Build a cost-optimized web app on OCI.`

Intent result: `cost`

Retrieved evidence:

- OCI Cost Management Overview
- OCI Well-Architected Framework
- OCI Object Storage Overview
- OCI CDN Overview
- OCI Compute Overview
- OCI Kubernetes Engine Overview

Quality assessment:

- Good cost-specific recommendations for rightsizing, autoscaling, Object Storage, lifecycle policies, budgets, tagging, and monitoring.
- Correctly calls out tradeoffs between cost, resilience, backups, and monitoring.
- Weak area: needs Budgets-specific source coverage, pricing/SKU awareness, and environment shutdown automation guidance.

### Release Awareness

Prompt: `How does the latest OCI update affect this architecture?`

Intent result: `release_awareness`

Retrieved evidence:

- OCI Architecture Center
- OCI Security Services Overview
- OCI Object Storage Overview
- OCI Well-Architected Framework
- OCI Database Services Overview
- OCI Database Migration Overview

Release context:

- Local release snapshot contains 3 release items.
- Release-aware response identifies potential context for Object Storage, Oracle Cloud Infrastructure, and Secret Management.
- Response correctly states that current impact must be verified against approved release snapshots.

Quality assessment:

- Good caution behavior: the system does not pretend old local knowledge is current truth.
- Weak area: release intelligence is not yet live, comprehensive, or integrated with selective reindexing.

## Deployment Consistency Review

ONE codebase / MULTIPLE environments discipline is preserved.

Current behavior:

- Local development and tests use the same backend, frontend, ingestion, eval, and retrieval code.
- Environment differences are expressed through configuration, Terraform variables, env files, and deployment scripts.
- No separate cloud-only application version was found.
- Sensitive staging values, Terraform plans, and SSH keys remain ignored.

Staging infrastructure plan:

- Target environment: `oci-architecture-studio-staging`
- Planned resources: 19 to add, 0 to change, 0 to destroy
- Compute shape: `VM.Standard.E5.Flex`
- Compute size: 8 OCPUs, 128 GB memory
- Image: Oracle Linux 9
- Notifications: `baba.shaik@oracle.com`

Risk:

- The cloud deployment has a prepared plan and validation path, but the Terraform apply and hosted smoke test are still operator-controlled steps.

## Operational Readiness Review

Current operational strengths:

- Backend exposes `/health`.
- Deployment smoke tests validate backend health, architecture review, release-aware review, frontend availability, and optional OCI SDK access.
- Terraform includes logging, monitoring, notification, and lifecycle event scaffolding.
- Deployment docs include config validation, Terraform flow, rollback basics, and smoke checks.
- CI includes backend tests, frontend build, evals, ingestion checks, and Terraform validation. Deployment orchestration should remain local/operator-run until OCI DevOps is introduced.

Operational gaps:

- No application log shipping from the FastAPI process into OCI Logging yet.
- No custom application metrics for retrieval latency, retrieval hit quality, eval drift, or citation coverage.
- No APM tracing or request correlation ID.
- Staging backend is planned to expose port `8000` directly; HTTPS ingress should be added before production/demo beyond sandbox usage.
- No automated rollback script has been executed against a live OCI deployment yet.

## Migration Risks

Main retrieval migration risks:

- OCI-native vector search may rank differently from the local JSON vector store.
- Embedding provider changes can alter eval behavior even when the corpus is unchanged.
- Citation fidelity can regress if chunk IDs, source URLs, or metadata are not preserved.
- Release-aware behavior can regress if release snapshots and knowledge chunks are mixed without source-type boundaries.
- OCI auth/config problems can make local development brittle if the adapter is not optional.

Main mitigation:

- Keep the local JSON vector store as a fallback.
- Add the OCI-native retriever behind a config flag.
- Dual-run local and OCI-native retrieval during migration.
- Require backend tests, golden evals, edge-case evals, ingestion smoke, release-ingestion smoke, and API smoke tests before changing defaults.

## Rollback Considerations

Rollback path:

1. Set retrieval provider back to the local JSON vector store.
2. Re-run knowledge ingestion with `--no-fetch` to regenerate the deterministic local index.
3. Re-run backend tests, golden evals, edge-case evals, and API smoke tests.
4. Keep OCI-native vector resources intact for inspection unless they caused cost or security issues.
5. Only delete cloud resources through Terraform after the failed migration state is understood.

## Go / No-Go Decision

Decision: **Go**

Conditions:

- Start with an adapter-level implementation only.
- Keep the current local retrieval path unchanged.
- Preserve existing metadata and citation contracts.
- Do not make OCI-native retrieval the default until golden evals, edge-case evals, and scenario spot checks pass in both local and OCI-native modes.

Recommended next milestone:

Build a production retrieval spike that adds an OCI-native vector adapter behind configuration, performs side-by-side retrieval comparisons, and produces a retrieval diff report for the five demo scenarios before switching any default behavior.
