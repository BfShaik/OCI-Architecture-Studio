# OCI Architecture Studio — Product Requirements Document

## Product Vision

OCI Architecture Studio is an AI-powered OCI architecture intelligence platform that provides grounded architecture guidance, migration advisory, cost optimization, and continuous OCI knowledge refresh.

## Current Product Capabilities

- Architecture Advisor
- Migration Advisor
- Cost Advisor
- Disaster Recovery Advisor
- Security Advisor
- Release-Aware Advisory
- Retrieval regression and parity validation
- OCI staging deployment

## Current Working Flow

The current implementation supports a validated API/UI advisory workflow with intent-aware orchestration, grounded retrieval, release-awareness scaffolding, and OCI staging deployment.

User flow:
1. A user asks an OCI architecture, migration, DR, cost, security, or release-awareness question.
2. The system classifies the prompt intent.
3. The system retrieves OCI knowledge chunks through a config-selected retrieval provider.
4. The system orchestrates a structured recommendation using the intent profile.
5. Release-aware prompts are checked against point-in-time release snapshots and freshness metadata.
6. The UI displays intent, prompt template, recommendations, assumptions, risks, citations, and next steps.

Current active staging retrieval:

- `local_json`

Validated promotion candidate:

- `oci_object_storage`
- parity passed against `local_json`
- promotion and rollback are config-only

Supported intents:
- product overview
- architecture
- migration
- disaster recovery
- cost
- security
- release awareness
- general

## Acceptance Criteria

- The backend exposes `GET /health`.
- The backend exposes `POST /architecture-review`.
- The backend exposes `GET /retrieval/health`.
- The architecture review response is structured and typed.
- The frontend can submit a question and render the response.
- Retrieval, intent classification, and orchestration are separated behind service modules.
- Prompt templates and golden eval prompts exist in source control.
- Golden prompts route to expected intents.
- Golden evals, edge-case evals, retrieval regression, and dual-provider parity can be run locally.
- OCI staging smoke tests validate backend, frontend, retrieval, and OCI SDK access.

## Current Non-Goals / Deferred Work

- No LangGraph implementation yet.
- No advanced memory or bi-temporal storage implementation yet.
- No full LLM synthesis yet.
- No continuous live release intelligence yet.
- Oracle AI Vector Search active reads remain guarded until schema, indexing, and query parity are validated.
- HTTPS ingress and production HA are deferred beyond the current staging slice.
