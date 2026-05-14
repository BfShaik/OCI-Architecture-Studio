# OCI Architecture Studio — Product Requirements Document

## Product Vision

OCI Architecture Studio is an AI-powered OCI architecture intelligence platform that provides grounded architecture guidance, migration advisory, cost optimization, and continuous OCI knowledge refresh.

## MVP Features

- Architecture Advisor
- Migration Advisor
- Cost Advisor
- Disaster Recovery Advisor
- Security Advisor
- Release-Aware Advisory

## MVP Vertical Slice

The first implementation focuses on a single API/UI workflow with local RAG and intent-aware orchestration.

User flow:
1. A user asks an OCI architecture question.
2. The system classifies the prompt intent.
3. The system retrieves local OCI knowledge chunks from the JSON vector index.
4. The system orchestrates a structured recommendation using the intent profile.
5. The UI displays intent, prompt template, recommendations, assumptions, risks, citations, and next steps.

Supported MVP intents:
- product overview
- architecture
- migration
- disaster recovery
- cost
- security
- release awareness
- general

## Initial Acceptance Criteria

- The backend exposes `GET /health`.
- The backend exposes `POST /architecture-review`.
- The architecture review response is structured and typed.
- The frontend can submit a question and render the response.
- Retrieval, intent classification, and orchestration are separated behind service modules.
- Prompt templates and golden eval prompts exist in source control.
- Golden prompts route to expected intents.

## Non-Goals

- No production vector database in the initial scaffold.
- No LangGraph implementation in the initial scaffold.
- No advanced memory or bi-temporal storage implementation in the initial scaffold.
- No automated OCI release ingestion in the initial scaffold.
- No full LLM synthesis in the initial scaffold.
