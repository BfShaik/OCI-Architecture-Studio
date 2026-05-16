# Architecture Diagrams

Date: 2026-05-16

These diagrams reflect the current code and staging runtime after OCI GenAI synthesis and OCI GenAI embedding promotion.

## 1. Runtime Architecture

```mermaid
flowchart TD
  User["Architect / Reviewer"] --> Gateway["OCI API Gateway"]
  Gateway --> Backend["FastAPI Backend\nOCI Compute VM"]
  Backend --> UI["React UI\nserved by backend"]

  Backend --> API["/architecture-review"]
  API --> Intent["Intent Classifier\narchitecture, migration, DR,\ncost, security, SaaS, release"]
  Intent --> Retrieval["Retrieval Pipeline\nservice mapping + heuristics + reranking"]

  Retrieval --> QueryEmbed["OCI GenAI Embedding\ncohere.embed-v4.0\nSEARCH_QUERY, 1536 dims"]
  QueryEmbed --> OracleVector["Oracle AI Vector Search\nOCI_ARCHITECTURE_CHUNKS_V4"]
  Retrieval -. rollback .-> ObjectStorage["OCI Object Storage\noci-rag-index.json\noci-rag-index.local-hash.json"]
  Retrieval -. local dev .-> LocalJson["Local JSON Snapshot"]

  Intent --> Orchestration["Controlled In-Process Orchestration\nsupervisor + specialists + critic"]
  Retrieval --> Orchestration
  Orchestration --> GenAIChat["OCI GenAI Chat\nxai.grok-4.3"]
  GenAIChat --> Response["Structured Advisory Response\nrecommendations, citations,\nconfidence, topology, governance"]
  Response --> UI

  Backend --> Ops["Operational APIs\n/health, /retrieval/health,\n/orchestration/health, /operations/*"]
```

## 2. Knowledge And Embedding Pipeline

```mermaid
flowchart LR
  Registry["knowledge/source_registry.json\napproved OCI sources"]
  Fetch["Fetch or registry fallback"]
  Chunk["Clean + chunk documents"]
  Metadata["Enrich metadata\nservice, domain, category,\nintent tags, migration mappings,\nfreshness, trust"]
  EmbedDocs["OCI GenAI Embedding\ncohere.embed-v4.0\nSEARCH_DOCUMENT, 1536 dims"]
  Manifest["Vector manifest\noci-rag-index.json"]
  ObjectStorage["Object Storage\nactive + rollback manifests"]
  OracleVector["Oracle AI Vector Search\nOCI_ARCHITECTURE_CHUNKS_V4"]
  Gates["Validation gates\nhealth, regression, golden, edge"]
  Promote["Runtime promotion\nVault/runtime env path"]

  Registry --> Fetch --> Chunk --> Metadata --> EmbedDocs --> Manifest
  Manifest --> Gates
  Gates --> ObjectStorage
  Gates --> OracleVector
  ObjectStorage --> Promote
  OracleVector --> Promote
```

Current promoted embedding metadata:

```text
embedding_provider=oci_genai
embedding_model=cohere.embed-v4.0
dimensions=1536
chunk_count=60
```

## 3. Retrieval Guardrail

```mermaid
flowchart TD
  Settings["Runtime settings\nprovider, model, dimensions"]
  StoreHealth["Index metadata\nprovider, model, dimensions"]
  Guardrail{"Do settings match index?"}
  Serve["Serve retrieval"]
  Refuse["Refuse retrieval\nsurface clear health error"]

  Settings --> Guardrail
  StoreHealth --> Guardrail
  Guardrail -->|yes| Serve
  Guardrail -->|no| Refuse
```

The guardrail prevents silent mismatches such as sending `cohere.embed-v4.0` query vectors to a 256-dimension local-hash index.

## 4. Advisory Orchestration

```mermaid
flowchart LR
  Prompt["Prompt"]
  Classifier["Intent classifier"]
  Evidence["Shared retrieved evidence"]
  Supervisor["Supervisor\nrouting decision"]
  Specialists["Specialists\narchitecture / migration /\nHA-DR / cost / release"]
  Synth["Final synthesizer\nsingle writer"]
  Critic["Validation critic\ngrounding, citations,\nfreshness, unsupported claims"]
  Response["API response"]

  Prompt --> Classifier --> Evidence --> Supervisor --> Specialists --> Synth --> Critic --> Response
  Evidence --> Synth
```

This is controlled in-process orchestration. It is not autonomous multi-agent execution, does not use long-running memory, and does not let specialists mutate citations independently.

## 5. Rollback Architecture

```mermaid
flowchart TD
  Current["Current live path\noci_genai + cohere.embed-v4.0\n1536 dims"]
  V4Table["OCI_ARCHITECTURE_CHUNKS_V4"]
  V4Manifest["Object Storage\noci-rag-index.json"]

  Rollback["Embedding rollback"]
  HashTable["OCI_ARCHITECTURE_CHUNKS\n256 dims"]
  HashManifest["Object Storage\noci-rag-index.local-hash.json"]
  Local["local_json emergency fallback"]

  Current --> V4Table
  Current --> V4Manifest
  Current -. config rollback .-> Rollback
  Rollback --> HashTable
  Rollback --> HashManifest
  Rollback -. emergency .-> Local
```

Rollback is intentionally config-only through the reviewed runtime path, followed by backend restart and `/retrieval/health` verification.

## 6. Release-Aware Refresh

```mermaid
flowchart TD
  Cron["VM cron\nrelease-watch"]
  ReleaseSources["OCI release sources"]
  Ingest["Release ingestion"]
  Classify["Impact classification\nservice, domain, change type"]
  Candidate["Candidate snapshot"]
  Gates["Quick gates + eval checks"]
  Promote["Promoted release snapshot"]
  Runtime["Architecture review runtime"]
  Answer["Response with temporal context"]

  Cron --> Ingest
  ReleaseSources --> Ingest --> Classify --> Candidate --> Gates
  Gates -->|pass| Promote --> Runtime
  Gates -->|fail| Runtime
  Runtime --> Answer
```

Release refresh never runs during a user query. User queries consume the last promoted release snapshot and freshness metadata.
