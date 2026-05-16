import {
  AlertTriangle,
  Activity,
  ArrowRight,
  Boxes,
  CalendarClock,
  Cloud,
  ClipboardCheck,
  Database,
  Download,
  Eye,
  Gauge,
  GitBranch,
  History,
  Layers,
  Network,
  Route,
  Scale,
  Search,
  Server,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import type {
  ArchitectureReviewResponse,
  ArchitectureTopologyNode,
  ArchitectureTopologyRelationship,
  MigrationPhasePlan,
} from "../types";

type ReviewResultProps = {
  result: ArchitectureReviewResponse;
};

function Section({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="result-section">
      <h3>{title}</h3>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function labelForIntent(intent: string) {
  return intent.replace(/_/g, " ");
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function readable(value: string) {
  return value.replace(/_/g, " ");
}

function answerSections(answer: string) {
  const sections = answer
    .split(/\n(?=\d+\.\s)/g)
    .map((section) => section.trim())
    .filter(Boolean);
  return sections.length > 1 ? sections : [answer];
}

function downloadMarkdown(title: string, markdown: string) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.md`;
  link.click();
  URL.revokeObjectURL(url);
}

function sourceLabelById(result: ArchitectureReviewResponse, chunkId: string) {
  const source = result.citations.find((citation) => citation.chunk_id === chunkId);
  return source?.service || source?.title || chunkId;
}

function displayList(values: string[], fallback = "None reported") {
  return values.length ? values.map(readable).join(", ") : fallback;
}

function displayTimestamp(value?: string | null) {
  if (!value) {
    return "Snapshot date not reported";
  }

  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(timestamp);
}

const topologyLanes = [
  {
    id: "access",
    title: "Access",
    roles: ["traffic-management", "edge-delivery", "edge-security", "ingress", "network"],
  },
  {
    id: "runtime",
    title: "Runtime",
    roles: ["application-runtime", "serverless-runtime", "event-stream", "supporting-service"],
  },
  {
    id: "data",
    title: "Data",
    roles: ["data", "storage", "data-pipeline"],
  },
  {
    id: "control",
    title: "Control",
    roles: ["identity", "security", "audit", "migration", "dr-orchestration"],
  },
  {
    id: "operations",
    title: "Operations",
    roles: ["observability", "operations"],
  },
];

function laneForRole(role: string) {
  return topologyLanes.find((lane) => lane.roles.includes(role)) ?? topologyLanes[1];
}

function topologyIcon(role: string) {
  if (["data", "storage", "data-pipeline"].includes(role)) {
    return <Database size={18} aria-hidden="true" />;
  }
  if (["identity", "security", "audit"].includes(role)) {
    return <ShieldCheck size={18} aria-hidden="true" />;
  }
  if (["observability", "operations"].includes(role)) {
    return <Eye size={18} aria-hidden="true" />;
  }
  if (["traffic-management", "edge-delivery", "edge-security", "ingress", "network"].includes(role)) {
    return <Network size={18} aria-hidden="true" />;
  }
  if (["migration", "dr-orchestration"].includes(role)) {
    return <Workflow size={18} aria-hidden="true" />;
  }
  if (["application-runtime", "serverless-runtime", "event-stream"].includes(role)) {
    return <Server size={18} aria-hidden="true" />;
  }
  return <Cloud size={18} aria-hidden="true" />;
}

function groupTopologyNodes(nodes: ArchitectureTopologyNode[]) {
  const groups = new Map(topologyLanes.map((lane) => [lane.id, [] as ArchitectureTopologyNode[]]));
  nodes.forEach((node) => {
    const lane = laneForRole(node.role);
    groups.get(lane.id)?.push(node);
  });
  return topologyLanes
    .map((lane) => ({
      ...lane,
      nodes: groups.get(lane.id) ?? [],
    }))
    .filter((lane) => lane.nodes.length);
}

function labelForNode(nodes: ArchitectureTopologyNode[], nodeId: string) {
  return nodes.find((node) => node.node_id === nodeId)?.label ?? readable(nodeId);
}

function relationshipSummary(nodes: ArchitectureTopologyNode[], relationship: ArchitectureTopologyRelationship) {
  return `${labelForNode(nodes, relationship.from_node)} to ${labelForNode(nodes, relationship.to_node)}`;
}

function migrationSteps(
  migrationFlow: string[] | undefined,
  phases: MigrationPhasePlan[] | undefined,
) {
  if (migrationFlow?.length) {
    return migrationFlow;
  }
  return phases?.map((phase) => phase.phase) ?? [];
}

function topologyNotes(notes: string[] | undefined) {
  return (notes ?? []).filter((note) => !note.toLowerCase().includes("not a rendered network diagram"));
}

export function ReviewResult({ result }: ReviewResultProps) {
  const citationCount = result.citations.length;
  const confidence = result.confidence;
  const experience = result.executive_experience;
  const visualization = experience?.architecture_visualization;
  const topology = result.architecture_topology;
  const optimization = result.optimization_plan;
  const topologyNodeGroups = groupTopologyNodes(topology?.nodes ?? []);
  const topologySteps = migrationSteps(visualization?.migration_flow, optimization?.migration_phases);
  const displayedTopologyNotes = topologyNotes(topology?.operational_notes);
  const reviewArtifact = experience?.review_artifacts[0];
  const governance = result.enterprise_governance;
  const releaseContext = result.release_context;
  const temporalContext = result.knowledge_temporal_context;
  const retrievalDebug = result.retrieval_debug;
  const firstDecision = experience?.decision_brief[0];
  const firstRisk = result.risks[0] ?? "No material risk was flagged by the current review.";
  const firstNextStep = result.next_steps[0] ?? "Confirm the architecture decision owner and implementation sequence.";
  const firstConfidenceNote =
    confidence?.notes[0] ?? "Confidence is based on retrieved OCI evidence and citation coverage.";

  return (
    <div className="review-result">
      <section className="answer-block advisory-overview">
        <div className="advisory-heading">
          <div>
            <p className="eyebrow review-eyebrow">AI Architecture Review</p>
            <h2>Architecture Review</h2>
          </div>
          <div className="review-score">
            <span>{confidence ? percent(confidence.overall) : "Pending"}</span>
            <small>{confidence ? `${confidence.level} confidence` : "confidence"}</small>
          </div>
        </div>
        <div className="intent-row">
          <span className="intent-badge">{labelForIntent(result.intent)}</span>
          <span>{citationCount} sources</span>
          <span>
            synthesis {result.synthesis_provider}
            {result.synthesis_fallback_used ? " fallback" : ""}
          </span>
          <span>orchestration {result.orchestration_mode}</span>
          {confidence ? (
            <span className={`confidence-badge confidence-${confidence.level}`}>
              confidence {confidence.level} · {percent(confidence.overall)}
            </span>
          ) : null}
          {result.not_enough_evidence ? <span className="warning-pill">needs evidence</span> : null}
          <span>{result.prompt_template}</span>
        </div>
        {experience ? <p className="executive-summary">{experience.executive_summary}</p> : null}
        <div className="answer-sections">
          {answerSections(result.answer).slice(0, 4).map((section, index) => (
            <p key={`answer-${index}`}>{section}</p>
          ))}
        </div>
        {result.quality_warnings.length ||
        result.synthesis_warnings.length ||
        result.orchestration_warnings.length ? (
          <div className="quality-warnings" aria-label="Quality warnings">
            {[...result.quality_warnings, ...result.synthesis_warnings, ...result.orchestration_warnings].map((warning, index) => (
              <span key={`warning-${index}-${warning}`}>{warning}</span>
            ))}
          </div>
        ) : null}
      </section>

      <section className="result-section release-context-panel">
        <div className="section-heading-row">
          <div>
            <h3>Release Context</h3>
            <p>Snapshot posture, release matches, affected services, and current-versus-historical guidance boundaries.</p>
          </div>
        </div>
        <div className="release-summary-grid">
          <article>
            <Activity size={18} aria-hidden="true" />
            <strong>{releaseContext?.matched_release_count ?? 0}</strong>
            <span>matched release item{releaseContext?.matched_release_count === 1 ? "" : "s"}</span>
          </article>
          <article>
            <Layers size={18} aria-hidden="true" />
            <strong>{releaseContext?.architecture_affecting_services.length ?? 0}</strong>
            <span>architecture-affecting service{releaseContext?.architecture_affecting_services.length === 1 ? "" : "s"}</span>
          </article>
          <article>
            <ClipboardCheck size={18} aria-hidden="true" />
            <strong>{releaseContext?.recommendation_affecting_services.length ?? 0}</strong>
            <span>recommendation-affecting service{releaseContext?.recommendation_affecting_services.length === 1 ? "" : "s"}</span>
          </article>
          <article>
            <CalendarClock size={18} aria-hidden="true" />
            <strong>{temporalContext ? readable(temporalContext.knowledge_mode) : "Current snapshot"}</strong>
            <span>{displayTimestamp(releaseContext?.snapshot_generated_at ?? temporalContext?.current_knowledge_as_of)}</span>
          </article>
        </div>
        <div className="release-detail-grid">
          <article>
            <strong>Affected Services</strong>
            <p>{displayList(releaseContext?.architecture_affecting_services ?? [])}</p>
          </article>
          <article>
            <strong>Impact Categories</strong>
            <p>{displayList(releaseContext?.impact_categories ?? [])}</p>
          </article>
          <article>
            <strong>Change Categories</strong>
            <p>{displayList(releaseContext?.change_categories ?? [])}</p>
          </article>
          <article>
            <strong>Temporal Boundary</strong>
            <p>{temporalContext?.notes[0] ?? "Current retrieval uses the active OCI knowledge snapshot."}</p>
          </article>
        </div>
        {(releaseContext?.maturity_notes.length || temporalContext?.notes.length) ? (
          <div className="release-notes">
            {[...(releaseContext?.maturity_notes ?? []), ...(temporalContext?.notes.slice(1, 3) ?? [])].map((note, index) => (
              <span key={`release-note-${index}`}>{note}</span>
            ))}
          </div>
        ) : null}
      </section>

      <section className="result-section decision-snapshot">
        <h3>Decision Snapshot</h3>
        <div className="snapshot-grid">
          <article>
            <Gauge size={18} aria-hidden="true" />
            <strong>{confidence ? percent(confidence.overall) : "Pending"}</strong>
            <span>{confidence ? `${confidence.level} confidence` : "confidence"}</span>
            <p>{firstConfidenceNote}</p>
          </article>
          <article>
            <ShieldCheck size={18} aria-hidden="true" />
            <strong>{governance ? readable(governance.maturity_level) : "Governance"}</strong>
            <span>{governance ? "review posture" : "not assessed"}</span>
            <p>{governance?.executive_summary.risk_summary ?? firstRisk}</p>
          </article>
          <article>
            <Route size={18} aria-hidden="true" />
            <strong>{firstDecision ? readable(firstDecision.implementation_priority) : "Next move"}</strong>
            <span>{firstDecision?.title ?? "implementation"}</span>
            <p>{firstDecision?.summary ?? firstNextStep}</p>
          </article>
          <article>
            <AlertTriangle size={18} aria-hidden="true" />
            <strong>{result.risks.length} risk{result.risks.length === 1 ? "" : "s"}</strong>
            <span>watch list</span>
            <p>{firstRisk}</p>
          </article>
        </div>
      </section>

      <section className="result-section explainability-dashboard">
        <div className="section-heading-row">
          <div>
            <h3>Explainability</h3>
            <p>Service choices, rejected paths, retrieval signals, governance influence, and release context.</p>
          </div>
        </div>
        <div className="influence-grid">
          <article>
            <Search size={18} aria-hidden="true" />
            <strong>Retrieval Influence</strong>
            <span>{confidence ? percent(confidence.retrieval) : "Not scored"}</span>
            <p>
              {retrievalDebug?.mapped_service_summary ||
                `${citationCount} retrieved source${citationCount === 1 ? "" : "s"} shaped the recommendation set.`}
            </p>
          </article>
          <article>
            <ShieldCheck size={18} aria-hidden="true" />
            <strong>Governance Influence</strong>
            <span>{governance ? readable(governance.maturity_level) : "Not assessed"}</span>
            <p>{governance?.executive_summary.governance_posture ?? "No governance constraints were elevated."}</p>
          </article>
          <article>
            <History size={18} aria-hidden="true" />
            <strong>Release Influence</strong>
            <span>{confidence ? percent(confidence.release_awareness) : "Not scored"}</span>
            <p>
              {releaseContext?.maturity_notes[0] ||
                temporalContext?.notes[0] ||
                "Guidance uses the active knowledge snapshot and release overlay when relevant."}
            </p>
          </article>
          <article>
            <Gauge size={18} aria-hidden="true" />
            <strong>Confidence Scoring</strong>
            <span>{confidence ? `${confidence.level} · ${percent(confidence.overall)}` : "Not scored"}</span>
            <p>{firstConfidenceNote}</p>
          </article>
        </div>

        {result.decision_reasoning.length ? (
          <div className="service-selection-list">
            {result.decision_reasoning.slice(0, 4).map((reason, index) => (
              <article key={`${reason.recommendation}-${reason.why_chosen}`}>
                <div>
                  <GitBranch size={18} aria-hidden="true" />
                  <span>Decision {index + 1}</span>
                </div>
                <strong>{reason.service ?? "Architecture decision"}</strong>
                <p>{reason.why_chosen}</p>
                {reason.workload_signal ? <small>{reason.workload_signal}</small> : null}
                <div className="explainability-tags">
                  <span>confidence {percent(reason.confidence)}</span>
                  {reason.source_chunk_ids.slice(0, 3).map((chunkId) => (
                    <span key={`${reason.recommendation}-${chunkId}`}>
                      {sourceLabelById(result, chunkId)}
                    </span>
                  ))}
                </div>
                {reason.alternatives_rejected.length ? (
                  <div className="rejected-paths">
                    <Scale size={16} aria-hidden="true" />
                    <p>Rejected: {reason.alternatives_rejected.slice(0, 2).join("; ")}</p>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        ) : null}

        {retrievalDebug ? (
          <div className="retrieval-trace">
            <article>
              <strong>Mapped Services</strong>
              <p>{retrievalDebug.mapped_oci_services.slice(0, 8).join(", ") || "None reported"}</p>
            </article>
            <article>
              <strong>Domain Signals</strong>
              <p>{retrievalDebug.domain_heuristics.slice(0, 8).map(readable).join(", ") || "None reported"}</p>
            </article>
            <article>
              <strong>Selected Evidence</strong>
              <p>
                {retrievalDebug.selected_final_chunks
                  .slice(0, 5)
                  .map((chunkId) => sourceLabelById(result, chunkId))
                  .join(", ") || "None reported"}
              </p>
            </article>
          </div>
        ) : null}
      </section>

      {experience ? (
        <section className="result-section executive-brief">
          <div className="section-heading-row">
            <div>
              <h3>Executive Brief</h3>
              <p>Review-ready decisions, implementation order, and governance context.</p>
            </div>
            {reviewArtifact ? (
              <button
                type="button"
                className="secondary-action"
                onClick={() => downloadMarkdown(reviewArtifact.title, reviewArtifact.markdown_summary)}
              >
                <Download size={16} aria-hidden="true" />
                Export Markdown
              </button>
            ) : null}
          </div>
          {governance?.recommendation_priorities.length ? (
            <div className="priority-strip">
              {governance.recommendation_priorities.slice(0, 4).map((item) => (
                <article key={`${item.recommendation_index}-${item.priority}`}>
                  <span>{readable(item.priority)}</span>
                  <strong>{item.implementation_phase}</strong>
                  <p>{item.rationale}</p>
                </article>
              ))}
            </div>
          ) : null}
          <div className="decision-grid">
            {experience.decision_brief.map((decision, index) => (
              <article key={`decision-${index}`}>
                <span>{readable(decision.implementation_priority)}</span>
                <h4>{decision.title}</h4>
                <p>{decision.summary}</p>
                <p>{decision.business_impact}</p>
                <small>{decision.risk_visibility}</small>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {experience?.implementation_sequence.length ? (
        <section className="result-section sequence-panel">
          <h3>Implementation Sequence</h3>
          <div className="sequence-list">
            {experience.implementation_sequence.map((phase) => (
              <article key={phase.phase}>
                <strong>{phase.phase}</strong>
                <p>{phase.objective}</p>
                <ul>
                  {phase.actions.slice(0, 3).map((action, index) => (
                    <li key={`${phase.phase}-action-${index}`}>{action}</li>
                  ))}
                </ul>
                {phase.exit_criteria.length ? (
                  <div className="exit-criteria">
                    {phase.exit_criteria.slice(0, 2).map((criterion, index) => (
                      <span key={`${phase.phase}-exit-${index}`}>{criterion}</span>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {visualization || topology ? (
        <section className="result-section topology-panel">
          <div className="section-heading-row">
            <div>
              <h3>Architecture Map</h3>
              <p>Service relationships, topology posture, HA/DR boundaries, and implementation flow.</p>
            </div>
          </div>
          <div className="topology-grid">
            <div>
              <h4>Topology</h4>
              <p>{visualization?.topology_summary ?? topology?.topology_summary}</p>
            </div>
            <div>
              <h4>Deployment</h4>
              <p>{visualization?.deployment_view ?? topology?.deployment_topology}</p>
            </div>
            <div>
              <h4>HA/DR</h4>
              <p>{visualization?.ha_dr_view ?? topology?.ha_dr_topology}</p>
            </div>
          </div>

          {topologyNodeGroups.length ? (
            <div className="topology-map" aria-label="Architecture service map">
              {topologyNodeGroups.map((lane, laneIndex) => (
                <article key={lane.id} className="topology-lane">
                  <div className="topology-lane-heading">
                    <span>{lane.title}</span>
                    {laneIndex < topologyNodeGroups.length - 1 ? <ArrowRight size={15} aria-hidden="true" /> : null}
                  </div>
                  <div className="topology-node-stack">
                    {lane.nodes.slice(0, 3).map((node) => (
                      <div key={node.node_id} className="topology-node-card">
                        {topologyIcon(node.role)}
                        <div>
                          <strong>{node.label}</strong>
                          <span>{readable(node.role)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          ) : null}

          {topology?.service_dependencies.length ? (
            <div className="relationship-board">
              <div className="relationship-board-heading">
                <Boxes size={18} aria-hidden="true" />
                <strong>Service Relationships</strong>
              </div>
              <div className="relationship-list">
                {topology.service_dependencies.slice(0, 6).map((relationship, index) => (
                  <article key={`${relationship.from_node}-${relationship.to_node}-${index}`}>
                    <span>{readable(relationship.relationship)}</span>
                    <strong>{relationshipSummary(topology.nodes, relationship)}</strong>
                    <p>{relationship.rationale}</p>
                  </article>
                ))}
              </div>
            </div>
          ) : null}

          {!topology?.service_dependencies.length && visualization?.dependency_summary.length ? (
            <div className="dependency-flow">
              {visualization.dependency_summary.slice(0, 6).map((dependency, index) => (
                <span key={`dependency-${index}`}>{dependency}</span>
              ))}
            </div>
          ) : null}

          {topologySteps.length ? (
            <ol className="migration-flow">
              {topologySteps.slice(0, 4).map((step, index) => (
                <li key={`flow-${index}-${step}`}>{step}</li>
              ))}
            </ol>
          ) : null}

          {displayedTopologyNotes.length ? (
            <div className="topology-notes">
              {displayedTopologyNotes.slice(0, 3).map((note, index) => (
                <span key={`topology-note-${index}`}>{note}</span>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {experience?.comparison_summary.length ? (
        <section className="result-section comparison-panel">
          <h3>Decision Comparisons</h3>
          <div className="comparison-list">
            {experience.comparison_summary.map((comparison, index) => (
              <article key={`comparison-${index}-${comparison.decision}`}>
                <div>
                  <strong>{comparison.decision}</strong>
                  <span>Prefer {comparison.preferred_option}</span>
                </div>
                <p>{comparison.operational_complexity}</p>
                <p>{comparison.cost_implications}</p>
                {comparison.pros.length || comparison.cons.length ? (
                  <div className="comparison-evidence">
                    {comparison.pros[0] ? <span>{comparison.pros[0]}</span> : null}
                    {comparison.cons[0] ? <span>{comparison.cons[0]}</span> : null}
                  </div>
                ) : null}
                {comparison.governance_implications.length ? (
                  <small>{comparison.governance_implications.slice(0, 2).join(" ")}</small>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {optimization ? (
        <section className="result-section optimization-panel">
          <div className="section-heading-row">
            <div>
              <h3>Migration & FinOps Optimization</h3>
              <p>{readable(optimization.maturity_level)}</p>
            </div>
          </div>
          {optimization.migration_phases.length ? (
            <div className="optimization-subsection">
              <h4>Migration Phases</h4>
              <div className="sequence-list">
                {optimization.migration_phases.map((phase) => (
                  <article key={phase.phase}>
                    <strong>{phase.phase}</strong>
                    <p>{phase.objective}</p>
                    <ul>
                      {phase.readiness_checks.slice(0, 2).map((check, index) => (
                        <li key={`${phase.phase}-check-${index}`}>{check}</li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {optimization.finops_recommendations.length ? (
            <div className="optimization-subsection">
              <h4>FinOps Levers</h4>
              <div className="comparison-list">
                {optimization.finops_recommendations.slice(0, 4).map((item) => (
                  <article key={item.lever}>
                    <div>
                      <strong>{item.lever}</strong>
                      <span>Cost control</span>
                    </div>
                    <p>{item.recommendation}</p>
                    <small>{item.expected_cost_implication}</small>
                  </article>
                ))}
              </div>
            </div>
          ) : null}
          {optimization.workload_optimization_signals.length ? (
            <div className="optimization-subsection">
              <h4>Workload Optimization</h4>
              <div className="topology-grid">
                {optimization.workload_optimization_signals.map((signal) => (
                  <div key={signal.workload}>
                    <h4>{signal.workload}</h4>
                    <p>{signal.scaling_guidance}</p>
                    <small>{signal.cost_performance_tradeoff}</small>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {optimization.implementation_readiness.length ? (
            <ul>
              {optimization.implementation_readiness.map((item, index) => (
                <li key={`readiness-${index}`}>{item}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {result.active_agents.length || result.critic_findings.length ? (
        <section className="result-section orchestration-panel">
          <h3>Controlled Orchestration</h3>
          {result.routing_decision ? <p>{result.routing_decision}</p> : null}
          {result.aggregation_decision ? <p>{result.aggregation_decision}</p> : null}
          {result.active_agents.length ? (
            <div className="agent-row">
              {result.active_agents.map((agent) => (
                <span key={agent}>{agent.replace(/_/g, " ")}</span>
              ))}
            </div>
          ) : null}
          {result.agent_contributions.length ? (
            <div className="agent-contributions">
              {result.agent_contributions.map((contribution) => (
                <article key={contribution.agent}>
                  <strong>{contribution.agent.replace(/_/g, " ")}</strong>
                  <span>{contribution.evidence_count} evidence chunks</span>
                  <p>{contribution.summary}</p>
                </article>
              ))}
            </div>
          ) : null}
          {result.critic_findings.length ? (
            <ul>
              {result.critic_findings.map((finding, index) => (
                <li key={`critic-${index}-${finding}`}>{finding}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {confidence ? (
        <section className="result-section confidence-panel">
          <h3>Confidence</h3>
          <div className="confidence-grid">
            <span>Retrieval {percent(confidence.retrieval)}</span>
            <span>Evidence {percent(confidence.evidence)}</span>
            <span>Freshness {percent(confidence.freshness)}</span>
            <span>Release {percent(confidence.release_awareness)}</span>
            <span>Recommendation {percent(confidence.recommendation)}</span>
            {typeof confidence.citation_coverage === "number" ? (
              <span>Citations {percent(confidence.citation_coverage)}</span>
            ) : null}
          </div>
          {confidence.notes.length ? (
            <ul>
              {confidence.notes.map((note, index) => (
                <li key={`confidence-note-${index}-${note}`}>{note}</li>
              ))}
            </ul>
          ) : null}
          {result.recommendation_confidence.length ? (
            <div className="recommendation-confidence-list">
              {result.recommendation_confidence.slice(0, 4).map((item, index) => (
                <article key={`${item.recommendation}-${index}`}>
                  <div>
                    <strong>{percent(item.score)}</strong>
                    <span>{item.level}</span>
                  </div>
                  <p>{item.recommendation}</p>
                  <small>{item.reasoning_basis}</small>
                </article>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      <div className="result-grid">
        <Section title="Recommendations" items={result.recommendations} />
        <Section title="Assumptions" items={result.assumptions} />
        <Section title="Risks" items={result.risks} />
        <Section title="Next Steps" items={result.next_steps} />
      </div>

      {experience?.explainability_highlights.length || result.decision_reasoning.length ? (
        <section className="result-section explainability-panel">
          <h3>Why This Recommendation</h3>
          {experience?.explainability_highlights.length ? (
            <ul>
              {experience.explainability_highlights.map((highlight, index) => (
                <li key={`highlight-${index}`}>{highlight}</li>
              ))}
            </ul>
          ) : null}
          {result.decision_reasoning.length ? (
            <div className="reasoning-list">
              {result.decision_reasoning.slice(0, 4).map((reason) => (
                <article key={`${reason.recommendation}-${reason.why_chosen}`}>
                  <strong>{reason.service ?? "Architecture decision"}</strong>
                  <p>{reason.why_chosen}</p>
                  {reason.alternatives_rejected.length ? (
                    <small>Alternatives: {reason.alternatives_rejected.slice(0, 2).join("; ")}</small>
                  ) : null}
                </article>
              ))}
            </div>
          ) : null}
          {result.architecture_tradeoffs.length ? (
            <div className="tradeoff-list">
              {result.architecture_tradeoffs.slice(0, 3).map((tradeoff) => (
                <article key={`${tradeoff.dimension}-${tradeoff.decision}`}>
                  <strong>{tradeoff.dimension}</strong>
                  <p>{tradeoff.decision}</p>
                  <small>{tradeoff.cost_or_risk}</small>
                </article>
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      {result.evidence_links.length ? (
        <section className="result-section evidence-links">
          <h3>Evidence Links</h3>
          {result.evidence_links.map((link) => (
            <article key={`${link.recommendation_index}-${link.support_level}`}>
              <strong>
                Recommendation {link.recommendation_index + 1}: {link.support_level}
              </strong>
              <p>{link.rationale}</p>
            </article>
          ))}
        </section>
      ) : null}

      <section className="result-section citations">
        <h3>Sources</h3>
        {result.citations.map((source, index) => (
          <article key={`${source.chunk_id ?? source.title}-${index}`} className="source-item">
            <div>
              <strong>{source.title}</strong>
              {source.service ? <span>{source.service}</span> : null}
              {source.service_domain ? <span>{source.service_domain}</span> : null}
              <span>
                {source.source_type}
                {typeof source.relevance_score === "number"
                  ? ` · ${source.relevance_score.toFixed(2)}`
                  : ""}
              </span>
              {typeof source.freshness_score === "number" ? (
                <span>freshness {source.freshness_score.toFixed(2)}</span>
              ) : null}
              {source.trust_level ? <span>{source.trust_level}</span> : null}
              {source.is_stale ? <span className="warning-pill">stale</span> : null}
            </div>
            {source.intent_tags.length || source.architecture_patterns.length ? (
              <div className="source-tags">
                {source.intent_tags.slice(0, 4).map((tag) => (
                  <span key={`${source.chunk_id}-intent-${tag}`}>{tag}</span>
                ))}
                {source.architecture_patterns.slice(0, 3).map((pattern) => (
                  <span key={`${source.chunk_id}-pattern-${pattern}`}>{pattern}</span>
                ))}
              </div>
            ) : null}
            <p>{source.summary}</p>
            {source.source_url ? (
              <a href={source.source_url} target="_blank" rel="noreferrer">
                Open source
              </a>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}
