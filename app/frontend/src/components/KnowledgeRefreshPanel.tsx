import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  RefreshCw,
  UploadCloud,
} from "lucide-react";
import type { KnowledgeRefreshStatus } from "../types";

type KnowledgeRefreshPanelProps = {
  status: KnowledgeRefreshStatus | null;
  error: string | null;
  isLoading: boolean;
  onRefresh: () => void;
};

function formatDate(value?: string | null): string {
  if (!value) {
    return "Not reported";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatText(value?: string | null): string {
  if (!value) {
    return "Not reported";
  }
  return value.replace(/_/g, " ");
}

function statusTone(status?: string, passed?: boolean): string {
  if (passed || status === "promoted" || status === "succeeded") {
    return "status-good";
  }
  if (status === "failed" || status === "blocked") {
    return "status-risk";
  }
  return "status-neutral";
}

export function KnowledgeRefreshPanel({
  status,
  error,
  isLoading,
  onRefresh,
}: KnowledgeRefreshPanelProps) {
  const lastRun = status?.last_run ?? null;
  const lifecycle = lastRun?.lifecycle ?? {};
  const snapshot = status?.current_promoted_snapshot ?? null;
  const lineage = snapshot?.lineage ?? {};
  const runStatus = lastRun?.status ?? status?.status ?? "unknown";
  const affectedSources = lastRun?.affected_source_ids ?? lineage.affected_source_ids ?? [];
  const releaseCount =
    lastRun?.changed_release_count ?? lineage.changed_release_ids?.length ?? 0;

  return (
    <section className="refresh-panel" aria-labelledby="refresh-panel-title">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow refresh-eyebrow">Operations</p>
          <h2 id="refresh-panel-title">Knowledge Refresh Status</h2>
        </div>
        <button
          type="button"
          className="secondary-action"
          onClick={onRefresh}
          disabled={isLoading}
          title="Reload knowledge refresh status"
        >
          <RefreshCw size={16} aria-hidden="true" />
          {isLoading ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="refresh-summary">
        <span className={`status-pill ${statusTone(runStatus, lastRun?.passed)}`}>
          {lastRun?.passed ? (
            <CheckCircle2 size={16} aria-hidden="true" />
          ) : (
            <AlertTriangle size={16} aria-hidden="true" />
          )}
          {formatText(runStatus)}
        </span>
        <span>
          <Clock3 size={16} aria-hidden="true" />
          Last run: {formatDate(lastRun?.started_at ?? snapshot?.started_at)}
        </span>
        <span>
          <UploadCloud size={16} aria-hidden="true" />
          Object Storage: {formatText(lifecycle.oci_upload_status)}
        </span>
        <span>
          <Database size={16} aria-hidden="true" />
          Snapshot: {formatText(lineage.knowledge_snapshot_version)}
        </span>
      </div>

      {error ? (
        <div className="refresh-error" role="alert">
          {error}
        </div>
      ) : null}

      <div className="refresh-grid">
        <article>
          <strong>Gate Result</strong>
          <p>{lifecycle.gates_run ? "Validation gates ran" : "No gate run reported"}</p>
          <small>
            {lastRun?.gates_passed || lifecycle.gates_passed
              ? "Passed"
              : "Not passed or not reported"}
          </small>
        </article>
        <article>
          <strong>Promotion</strong>
          <p>{formatText(lifecycle.promotion_status ?? snapshot?.status)}</p>
          <small>
            Authoritative snapshots{" "}
            {lifecycle.authoritative_snapshots_updated ? "updated" : "not updated"}
          </small>
        </article>
        <article>
          <strong>Release Changes</strong>
          <p>{releaseCount} release items</p>
          <small>{affectedSources.length} affected sources</small>
        </article>
        <article>
          <strong>Rollback</strong>
          <p>{lifecycle.rollback_available ? "Available" : "Not reported"}</p>
          <small>{lastRun?.rollback_performed ? "Rollback performed" : "No rollback performed"}</small>
        </article>
      </div>
    </section>
  );
}
