# Demo Readiness

Last updated: 2026-05-17

## Demo Status

The app is ready for a controlled team demo in staging.

| Area | Status |
| --- | --- |
| Frontend | Ready |
| Backend | Ready |
| OCI GenAI synthesis | Active |
| Oracle AI Vector Search | Active |
| OCI GenAI embeddings | Active |
| Citations/evidence links | Ready |
| Rollback paths | Ready |

## Suggested 10-Minute Demo

1. Open the staging app.
2. Submit:

```text
How should I deploy a stateless web app on OCI?
```

3. Show that the prompt/options area stays at the top.
4. Walk through summary, recommendations, risks, and citations.
5. Click one evidence/source link.
6. Explain the runtime flags:

```text
ADVISORY_SYNTHESIS_PROVIDER=oci_genai
RETRIEVAL_PROVIDER=oracle_ai_vector_search
EMBEDDING_PROVIDER=oci_genai
```

## Good Backup Prompts

```text
Design a highly available ecommerce platform on OCI.
```

```text
Migrate EKS and RDS to OCI.
```

```text
Recommend OCI services for fintech disaster recovery.
```

```text
Build a cost-optimized web app on OCI.
```

## What To Say If Asked

**Is it hardcoded?**

No. The response shape is controlled, but recommendations are based on the user prompt, retrieved OCI evidence, and OCI GenAI synthesis.

**Is this RAG?**

Yes, it follows a RAG pattern: retrieve OCI evidence first, then synthesize a grounded answer.

**Can we turn GenAI off?**

Yes. Set:

```text
ADVISORY_SYNTHESIS_PROVIDER=deterministic
```

## Known Demo Limits

- The corpus is curated, not a full OCI documentation mirror.
- Release awareness uses snapshots, not live request-time release reconciliation.
- Team-real prompt evals still need to be restored or created.
