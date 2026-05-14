# OCI Architecture Studio — Golden Prompts

## Purpose

Use this file as the first regression suite for OCI Architecture Studio.
Each prompt should verify:

- intent match
- OCI specificity
- grounding
- structure
- non-hallucination

---

## Phase 1 — Foundation

### Prompt

What does OCI Architecture Studio do?

### Expected intent

Product overview

### Expected response traits

- explains the product clearly
- mentions architecture guidance, migration, cost, and release-aware knowledge
- avoids generic chatbot language
- avoids invented OCI services

### Pass condition

The response is accurate, consistent, and clearly describes the product.

---

## Phase 2 — Basic Architecture

### Prompt

Design a highly available ecommerce platform on OCI.

### Expected intent

Architecture design

### Expected response traits

- storefront or web tier
- load balancing
- database tier
- object storage or CDN where relevant
- HA and DR considerations
- risks and assumptions

### Pass condition

The answer is specific to ecommerce and not generic OCI advice.

---

## Phase 3 — Migration

### Prompt

Migrate EKS + RDS to OCI.

### Expected intent

Migration mapping

### Expected response traits

- maps EKS to OKE
- maps RDS to OCI database options
- mentions migration phases
- identifies risks and dependencies
- includes modernization guidance

### Pass condition

The answer is clearly migration-oriented and service mapping is correct.

---

## Phase 4 — Disaster Recovery

### Prompt

Recommend OCI services for fintech DR.

### Expected intent

Resilience / DR planning

### Expected response traits

- cross-region resilience
- backup / replication / failover
- DNS or traffic steering if relevant
- Vault, Logging, Monitoring, security controls
- compliance-aware thinking

### Pass condition

The answer focuses on DR rather than general architecture.

---

## Phase 5 — Cost Optimization

### Prompt

Build a cost-optimized web app on OCI.

### Expected intent

Cost optimization

### Expected response traits

- rightsizing
- autoscaling
- object storage where appropriate
- budgets and monitoring
- performance vs cost tradeoffs
- avoids overprovisioning

### Pass condition

The answer gives concrete cost actions.

---

## Phase 6 — Release Awareness

### Prompt

How does the latest OCI update affect this architecture?

### Expected intent

Time-aware advisory

### Expected response traits

- asks for or uses current release context
- identifies whether the update affects the recommendation
- separates current knowledge from historical knowledge when needed

### Pass condition

The response is time-aware and does not treat old knowledge as current truth.

---

## Review checklist

For every response, check:

1. Intent match
2. OCI specificity
3. Grounding
4. Structure
5. Non-hallucination

---

## Notes

Store this file in `evals/` and keep it small.
Add more prompts only when a real failure appears.
