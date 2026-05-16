# OCI Architecture Studio — Architecture Diagrams

Date: 2026-05-16

These diagrams summarize the current working platform, the completed Oracle AI Vector Search active-read promotion, the Object Storage rollback path, release-awareness, and operational control points.

## 1. Current Working Staging Architecture

Current staging is intentionally simple: one codebase, one backend VM, backend-served frontend, Oracle AI Vector Search active retrieval, Object Storage rollback snapshots, and OCI services for deployment support, snapshots, secrets, logging, monitoring, and notifications.

```mermaid
flowchart LR
  User["Architect / User"]

  subgraph OCI["OCI us-ashburn-1"]
    subgraph Compartment["oci-architecture-studio-staging compartment"]
      VM["Compute VM\nFastAPI backend + served React frontend\nVM.Standard.E5.Flex\n8 OCPU / 128 GB"]
      LocalIndex["Local JSON knowledge index\nrollback provider"]
      ObjectIndex["Object Storage vector manifest\nrollback snapshot\noci-rag-index.json"]
      VectorIndex["Oracle AI Vector Search\nactive retrieval provider\n60 chunks"]
      ReleaseSnap["Local release snapshot\noci-release-snapshot.json"]
      FrontendBucket["Object Storage\nfrontend assets"]
      SnapshotBucket["Object Storage\nknowledge + release snapshots"]
      Vault["OCI Vault\nruntime config / secrets"]
      Logs["OCI Logging\napp and deployment logs"]
      Monitoring["OCI Monitoring\nbackend CPU alarm"]
      Events["OCI Events + Notifications\nresource lifecycle alerts"]
      Cron["VM cron\nrelease-watch active\nstable-docs safe mode"]
    end
  end

  User -->|"HTTP staging URL"| VM
  VM -->|"serves React UI"| User
  VM -->|"architecture-review API\nactive read"| VectorIndex
  VM -. "config rollback" .-> ObjectIndex
  VM -. "config rollback" .-> LocalIndex
  VM -->|"release-aware context"| ReleaseSnap
  VM -. "snapshot sync / backup" .-> SnapshotBucket
  VM -. "frontend artifact upload path" .-> FrontendBucket
  VM -. "secrets access" .-> Vault
  VM -. "logs" .-> Logs
  Monitoring --> Events
  Cron --> SnapshotBucket
  Cron --> ObjectIndex
  ObjectIndex --> VectorIndex
```

Current active retrieval provider:

```text
RETRIEVAL_PROVIDER=oracle_ai_vector_search
```

## 2. Validated Retrieval Promotion Path

OCI Object Storage first passed parity against the stable local provider, then Oracle AI Vector Search passed active-read parity and was promoted in staging. Rollback to Object Storage and local JSON remains config-only.

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
  VectorGate["Oracle vector active-read gate\nparity + regression + smoke"]
  Promote["Completed staging promotion\nRETRIEVAL_PROVIDER=oracle_ai_vector_search"]
  Rollback["Config-only rollback\nRETRIEVAL_PROVIDER=oci_object_storage or local_json"]

  Prompt --> Classifier --> Query
  Query --> LocalEmbed --> LocalStore --> LocalResults --> Parity
  Query --> OCIEmbed --> ObjectStore --> OCIStore --> OCIResults --> Parity
  Parity --> EvalGate --> VectorGate
  VectorGate --> Promote
  Promote --> Rollback
```

Validated parity result:

- `local_json`: passed
- `oci_object_storage`: passed
- `oracle_ai_vector_search`: passed active-read promotion gates
- parity cases: `14/14`
- golden evals: `6/6` for both provider paths
- edge-case evals: `8/8` for both provider paths
- retrieval regression: `14/14` for both provider paths
- staging active provider: `oracle_ai_vector_search`
- rollback providers: `oci_object_storage`, then `local_json`

## 3. Current OCI-Native Retrieval Architecture

Oracle AI Vector Search is the active staging read path. Object Storage remains the promoted manifest store and immediate rollback provider.

```mermaid
flowchart LR
  Sources["Approved OCI docs\nsource registry"]
  Releases["OCI release sources\nrelease registry"]
  Scheduler["Backend OCI VM cron\ncurrent release-watch scheduler"]

  subgraph Ingestion["Knowledge Refresh Pipeline"]
    Fetch["Fetch or fallback"]
    Clean["Clean boilerplate"]
    Chunk["Chunk documents"]
    Metadata["Add metadata\nservice, domain, intent tags,\nfreshness, trust, content hash"]
    Embed["OCI Generative AI embeddings"]
    Candidate["Candidate snapshots\nrun-scoped"]
    Gates["Retrieval + eval gates"]
    Promote["Promote only if gates pass"]
  end

  subgraph Storage["OCI Knowledge Storage"]
    Raw["Object Storage\nraw/source snapshots"]
    Manifest["Object Storage\nmigration-safe vector manifest"]
    Vector["Oracle AI Vector Search\nactive read path"]
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

  Scheduler --> Fetch
  Sources --> Fetch --> Clean --> Chunk --> Metadata --> Embed --> Candidate --> Gates --> Promote
  Metadata --> Raw
  Promote --> Manifest
  Promote --> Vector
  Releases --> ReleaseStore

  UI --> API --> Intent --> Retriever
  Retriever --> Vector
  Retriever -. "rollback" .-> Manifest
  Retriever --> Freshness
  ReleaseStore --> Freshness
  Freshness --> Response --> UI
```

Migration sequence:

1. Keep `local_json` as rollback provider.
2. Promote `oci_object_storage` as active staging provider after parity. — Done
3. Validate staging smoke and evals. — Done
4. Implement Oracle AI Vector Search table/index. — Done
5. Dual-run Vector Search against `oci_object_storage`. — Done
6. Promote Oracle AI Vector Search after parity and rollback validation. — Done

## 4. Continuous Release-Awareness Flow

Release-awareness is a differentiator because release context is stored separately from normal architecture knowledge. The system can avoid treating old architecture guidance as current release truth.

```mermaid
flowchart TD
  Scheduler["VM cron release watcher"]
  ReleaseIngest["Release ingestion"]
  Classify["Classify service, domain, impact"]
  Candidate["Candidate release + knowledge snapshots"]
  Gates["Eval and retrieval gates"]
  Promote["Promoted authoritative snapshot"]
  Status["/knowledge/refresh/status"]
  UserPrompt["User asks about latest OCI update"]
  Intent["Intent classifier\nrelease_awareness"]
  Knowledge["Architecture retrieval\ncurrent promoted snapshot"]
  ReleaseSnapshot["Point-in-time release snapshot"]
  FreshnessCheck["Freshness / staleness check"]
  Answer["Response separates\ncurrent guidance from release-sensitive guidance"]

  Scheduler --> ReleaseIngest --> Classify --> Candidate --> Gates
  Gates -->|pass| Promote --> Status
  Gates -->|fail| Status
  UserPrompt --> Intent
  Intent --> Knowledge
  Intent --> ReleaseSnapshot
  Promote --> Knowledge
  Promote --> ReleaseSnapshot
  Knowledge --> FreshnessCheck
  ReleaseSnapshot --> FreshnessCheck
  FreshnessCheck --> Answer
```

Current release-awareness maturity:

- point-in-time release snapshot exists
- scheduled release watcher runs from backend OCI VM cron
- candidate-first refresh and eval-gated promotion exist
- release-aware intent exists
- stale-source caution exists
- deeper semantic impact analysis remains future work

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

## 6. Controlled Multi-Agent Advisory Orchestration

The current agent foundation is controlled and in-process. It adds bounded specialist collaboration and critic visibility while preserving the same retrieval, synthesis, and eval paths.

```mermaid
flowchart LR
  Prompt["User prompt"]
  Classifier["Intent classifier"]
  Evidence["Shared retrieval evidence"]
  Supervisor["Supervisor\nrouting decision"]
  Specialists["Selected specialists\narchitecture / migration / HA-DR / cost / release"]
  Aggregator["Final synthesizer\nsingle-writer response"]
  Synth["Configured synthesis provider\ndeterministic or OCI GenAI"]
  Quality["Citation + confidence analyzer"]
  Critic["Validation critic\ngrounding, citations, freshness,\nunsupported claims"]
  Response["Structured response\nactive agents, critic findings,\nconfidence, citations"]

  Prompt --> Classifier --> Evidence --> Supervisor --> Specialists --> Aggregator --> Synth --> Quality --> Critic --> Response
```

Rollback remains config-only:

```text
ADVISORY_ORCHESTRATION_MODE=supervised
ADVISORY_ORCHESTRATION_MODE=single_pass
```

Deferred by design:

- autonomous agent swarms
- distributed orchestration frameworks
- agent-specific memory
- provider-specific agent code paths
