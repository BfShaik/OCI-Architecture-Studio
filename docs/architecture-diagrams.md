# OCI Architecture Studio — Architecture Diagrams

Date: 2026-05-15

These diagrams summarize the current working platform, the validated retrieval migration path, and the next Oracle AI Vector Search target state.

## 1. Current Working Staging Architecture

Current staging is intentionally simple: one codebase, one backend VM, backend-served frontend, local JSON retrieval on the VM, and OCI services for deployment support, snapshots, secrets, logging, monitoring, and notifications.

```mermaid
flowchart LR
  User["Architect / User"]

  subgraph OCI["OCI us-ashburn-1"]
    subgraph Compartment["oci-architecture-studio-staging compartment"]
      VM["Compute VM\nFastAPI backend + served React frontend\nVM.Standard.E5.Flex\n8 OCPU / 128 GB"]
      LocalIndex["Local JSON knowledge index\n/opt/oci-architecture-studio/knowledge/snapshots/oci-rag-index.json"]
      ReleaseSnap["Local release snapshot\noci-release-snapshot.json"]
      FrontendBucket["Object Storage\nfrontend assets"]
      SnapshotBucket["Object Storage\nknowledge + release snapshots"]
      Vault["OCI Vault\nruntime config / secrets"]
      Logs["OCI Logging\napp and deployment logs"]
      Monitoring["OCI Monitoring\nbackend CPU alarm"]
      Events["OCI Events + Notifications\nresource lifecycle alerts"]
    end
  end

  User -->|"HTTP staging URL"| VM
  VM -->|"serves React UI"| User
  VM -->|"architecture-review API"| LocalIndex
  VM -->|"release-aware context"| ReleaseSnap
  VM -. "snapshot sync / backup" .-> SnapshotBucket
  VM -. "frontend artifact upload path" .-> FrontendBucket
  VM -. "secrets access" .-> Vault
  VM -. "logs" .-> Logs
  Monitoring --> Events
```

Current active retrieval provider:

```text
RETRIEVAL_PROVIDER=local_json
```

## 2. Validated Dual-Provider Retrieval Migration Path

The OCI Object Storage retrieval provider has passed parity against the stable local provider. Promotion is config-only and rollback is also config-only.

```mermaid
flowchart TD
  Prompt["User prompt"]
  Classifier["Intent classifier"]
  Query["Intent-expanded retrieval query"]

  subgraph Local["Baseline Provider"]
    LocalEmbed["LocalHashingEmbedder"]
    LocalStore["JsonVectorStore\nlocal oci-rag-index.json"]
    LocalResults["RetrievedSource citations"]
  end

  subgraph OCIManifest["OCI-Native Manifest Provider"]
    OCIEmbed["LocalHashingEmbedder\nsame embedding contract for parity"]
    ObjectStore["OCI Object Storage\noci-rag-index.json"]
    OCIStore["OciObjectStorageVectorStore\ncached manifest"]
    OCIResults["RetrievedSource citations"]
  end

  Parity["Retrieval parity gate\n14/14 passed\n1.0 top chunk overlap"]
  EvalGate["Golden + edge evals\nretrieval regression\nsmoke tests"]
  Promote["Config-only staging promotion\nRETRIEVAL_PROVIDER=oci_object_storage"]
  Rollback["Config-only rollback\nRETRIEVAL_PROVIDER=local_json"]

  Prompt --> Classifier --> Query
  Query --> LocalEmbed --> LocalStore --> LocalResults --> Parity
  Query --> OCIEmbed --> ObjectStore --> OCIStore --> OCIResults --> Parity
  Parity --> EvalGate
  EvalGate --> Promote
  Promote --> Rollback
```

Validated parity result:

- `local_json`: passed
- `oci_object_storage`: passed
- parity cases: `14/14`
- golden evals: `6/6` for both provider paths
- edge-case evals: `8/8` for both provider paths
- retrieval regression: `14/14` for both provider paths

## 3. Target OCI-Native Retrieval Architecture

This is the next production retrieval target. Oracle AI Vector Search remains guarded until schema, indexing, query behavior, and parity are validated.

```mermaid
flowchart LR
  Sources["Approved OCI docs\nsource registry"]
  Releases["OCI release sources\nrelease registry"]

  subgraph Ingestion["Knowledge Refresh Pipeline"]
    Fetch["Fetch or fallback"]
    Clean["Clean boilerplate"]
    Chunk["Chunk documents"]
    Metadata["Add metadata\nservice, domain, intent tags,\nfreshness, trust, content hash"]
    Embed["OCI Generative AI embeddings"]
  end

  subgraph Storage["OCI Knowledge Storage"]
    Raw["Object Storage\nraw/source snapshots"]
    Manifest["Object Storage\nmigration-safe vector manifest"]
    Vector["Oracle AI Vector Search\nguarded future read path"]
    ReleaseStore["Object Storage\nrelease snapshots"]
  end

  subgraph Runtime["Advisory Runtime"]
    UI["React UI"]
    API["FastAPI backend"]
    Intent["Intent-aware orchestration"]
    Retriever["Retrieval adapter\nconfig-selected provider"]
    Freshness["Freshness + release checks"]
    Response["Structured advisory response\nrecommendations, risks, citations"]
  end

  Sources --> Fetch --> Clean --> Chunk --> Metadata --> Embed
  Metadata --> Raw
  Embed --> Manifest
  Embed -. "future active read path" .-> Vector
  Releases --> ReleaseStore

  UI --> API --> Intent --> Retriever
  Retriever --> Manifest
  Retriever -. "future" .-> Vector
  Retriever --> Freshness
  ReleaseStore --> Freshness
  Freshness --> Response --> UI
```

Promotion sequence:

1. Keep `local_json` as rollback provider.
2. Promote `oci_object_storage` as active staging provider after parity.
3. Validate staging smoke and evals.
4. Implement Oracle AI Vector Search table/index.
5. Dual-run Vector Search against `oci_object_storage`.
6. Promote Oracle AI Vector Search only after parity and rollback validation.

## 4. Release-Awareness Flow

Release-awareness is a differentiator because release context is stored separately from normal architecture knowledge. The system can avoid treating old architecture guidance as current release truth.

```mermaid
flowchart TD
  UserPrompt["User asks about latest OCI update"]
  Intent["Intent classifier\nrelease_awareness"]
  Knowledge["Normal architecture retrieval\ncurrent knowledge snapshot"]
  ReleaseSnapshot["Release snapshot store\npoint-in-time release knowledge"]
  FreshnessCheck["Freshness / staleness check"]
  Answer["Response separates\nhistorical guidance from release-sensitive guidance"]
  NextStep["Ask for release note or refresh snapshot\nbefore definitive impact claim"]

  UserPrompt --> Intent
  Intent --> Knowledge
  Intent --> ReleaseSnapshot
  Knowledge --> FreshnessCheck
  ReleaseSnapshot --> FreshnessCheck
  FreshnessCheck --> Answer --> NextStep
```

Current release-awareness maturity:

- point-in-time release snapshot exists
- release-aware intent exists
- stale-source caution exists
- full continuous release watcher and impact analyzer are still future work

## 5. Operational Control Points

```mermaid
flowchart LR
  Dev["Local dev/test"]
  CI["CI gates\nbackend, frontend, evals,\ningestion, retrieval"]
  Stage["OCI staging"]
  Smoke["Smoke tests\nhealth, UI, API, OCI SDK"]
  Guardrails["Retrieval parity\nrelease checks\nrollback checks"]
  Promote["Config promotion"]
  Rollback["Config rollback"]

  Dev --> CI --> Stage --> Smoke --> Guardrails --> Promote
  Promote --> Rollback
  Rollback --> Stage
```

Core operating rule:

```text
ONE codebase / MULTIPLE environments
Local = development and testing
OCI = staging, demo, production
Provider changes happen through config, not code forks.
```
