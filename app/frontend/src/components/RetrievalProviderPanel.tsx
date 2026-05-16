import {
  AlertTriangle,
  CheckCircle2,
  Database,
  FileJson,
  HardDrive,
  RefreshCw,
} from "lucide-react";
import type { RetrievalHealth, RetrievalStoreHealth } from "../types";

type RetrievalProviderPanelProps = {
  health: RetrievalHealth | null;
  error: string | null;
  isLoading: boolean;
  onRefresh: () => void;
};

function formatText(value?: string | null): string {
  if (!value) {
    return "Not reported";
  }
  return value.replace(/_/g, " ");
}

function formatCount(value?: number): string {
  return typeof value === "number" ? value.toLocaleString() : "0";
}

function activeStore(store?: RetrievalStoreHealth): RetrievalStoreHealth | null {
  if (!store) {
    return null;
  }
  if (store.primary || store.fallback) {
    return store.fallback_active ? store.fallback ?? store : store.primary ?? store;
  }
  return store;
}

function objectStorageLabel(store: RetrievalStoreHealth | null): string {
  const candidates = [store, store?.primary, store?.fallback].filter(Boolean) as RetrievalStoreHealth[];
  const objectStore = candidates.find((candidate) =>
    candidate.provider?.includes("object_storage"),
  );

  if (!objectStore) {
    return "Not active";
  }

  if (objectStore.bucket && objectStore.object_name) {
    return `${objectStore.bucket}/${objectStore.object_name}`;
  }

  return formatText(objectStore.provider);
}

function oracleVectorLabel(health: RetrievalHealth | null): string {
  const store = health?.store;
  const candidates = [store?.primary, store, store?.fallback].filter(Boolean) as RetrievalStoreHealth[];
  const oracleStore = candidates.find((candidate) =>
    candidate.provider?.includes("oracle_ai_vector_search"),
  );

  if (!oracleStore) {
    return health?.provider === "oracle_ai_vector_search" ? "Configured" : "Shadow only";
  }

  if (oracleStore.read_enabled) {
    return health?.provider === "oracle_ai_vector_search" ? "Active read path" : "Read path enabled";
  }

  if (oracleStore.schema?.valid) {
    return "Shadow index valid";
  }

  if (oracleStore.missing_config?.length) {
    return "Missing configuration";
  }

  return "Shadow only";
}

function statusTone(exists?: boolean, fallbackActive?: boolean): string {
  if (fallbackActive) {
    return "status-risk";
  }
  if (exists) {
    return "status-good";
  }
  return "status-neutral";
}

export function RetrievalProviderPanel({
  health,
  error,
  isLoading,
  onRefresh,
}: RetrievalProviderPanelProps) {
  const store = health?.store ?? null;
  const selectedStore = activeStore(store ?? undefined);
  const fallbackActive = Boolean(store?.fallback_active);
  const provider = health?.provider ?? selectedStore?.provider ?? "unknown";
  const chunkCount = selectedStore?.chunk_count ?? store?.chunk_count ?? 0;

  return (
    <section className="refresh-panel" aria-labelledby="retrieval-panel-title">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow refresh-eyebrow">Retrieval</p>
          <h2 id="retrieval-panel-title">Retrieval Provider Status</h2>
        </div>
        <button
          type="button"
          className="secondary-action"
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload retrieval provider status"
        >
          <RefreshCw size={16} aria-hidden="true" />
          {isLoading ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="refresh-summary">
        <span className={`status-pill ${statusTone(store?.exists, fallbackActive)}`}>
          {store?.exists ? (
            <CheckCircle2 size={16} aria-hidden="true" />
          ) : (
            <AlertTriangle size={16} aria-hidden="true" />
          )}
          {formatText(provider)}
        </span>
        <span>
          <FileJson size={16} aria-hidden="true" />
          Chunks: {formatCount(chunkCount)}
        </span>
        <span>
          <HardDrive size={16} aria-hidden="true" />
          Fallback: {fallbackActive ? "Active" : store?.fallback_enabled ? "Available" : "Not active"}
        </span>
        <span>
          <Database size={16} aria-hidden="true" />
          Oracle vector: {oracleVectorLabel(health)}
        </span>
      </div>

      {error ? (
        <div className="refresh-error" role="alert">
          {error}
        </div>
      ) : null}

      <div className="refresh-grid">
        <article>
          <strong>Active Store</strong>
          <p>{formatText(selectedStore?.provider ?? store?.provider)}</p>
          <small>{selectedStore?.exists || store?.exists ? "Store reachable" : "Not reachable"}</small>
        </article>
        <article>
          <strong>Object Storage</strong>
          <p>{objectStorageLabel(store)}</p>
          <small>{store?.primary?.namespace ?? selectedStore?.namespace ?? "Namespace not reported"}</small>
        </article>
        <article>
          <strong>Coverage</strong>
          <p>{formatCount(selectedStore?.service_count ?? store?.service_count)} services</p>
          <small>{formatCount(selectedStore?.service_domain_count ?? store?.service_domain_count)} domains</small>
        </article>
        <article>
          <strong>Runtime</strong>
          <p>{formatText(health?.embedding_model)}</p>
          <small>
            {fallbackActive
              ? formatText(store?.fallback_reason ?? "primary provider unavailable")
              : "Primary provider serving reads"}
          </small>
        </article>
      </div>
    </section>
  );
}
