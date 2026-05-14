# OCI Architecture Studio — Product Requirements Document

## Product Vision

OCI Architecture Studio is an AI-powered OCI architecture intelligence platform that provides grounded architecture guidance, migration advisory, cost optimization, and continuous OCI knowledge refresh.

## MVP Features

- Architecture Advisor
- Migration Advisor
- Cost Advisor
- Release Intelligence System
- Bi-Temporal Memory

## MVP Vertical Slice

The first implementation focuses on Architecture Advisor only.

User flow:
1. A user asks an OCI architecture question.
2. The system retrieves placeholder OCI knowledge records.
3. The system orchestrates a structured recommendation.
4. The UI displays recommendations, assumptions, risks, citations, and next steps.

## Initial Acceptance Criteria

- The backend exposes `GET /health`.
- The backend exposes `POST /architecture-review`.
- The architecture review response is structured and typed.
- The frontend can submit a question and render the response.
- Retrieval and orchestration are separated behind service modules.
- Prompt and eval starter files exist in source control.

## Non-Goals

- No production RAG pipeline in the initial scaffold.
- No LangGraph implementation in the initial scaffold.
- No advanced memory or bi-temporal storage implementation in the initial scaffold.
- No automated OCI release ingestion in the initial scaffold.
