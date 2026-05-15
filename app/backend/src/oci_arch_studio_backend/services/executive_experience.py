from __future__ import annotations

from oci_arch_studio_backend.models.architecture import (
    ArchitectureComparison,
    ArchitectureDecisionReason,
    ArchitectureReviewArtifact,
    ArchitectureTopologySummary,
    ArchitectureTradeoffAnalysis,
    ExecutiveDecisionBrief,
    ExecutiveExperienceSummary,
    ImplementationSequenceItem,
    ArchitectureVisualizationSummary,
    ConfidenceScore,
    EnterpriseGovernanceAssessment,
    EvidenceLink,
    RecommendationConfidenceIndicator,
    RetrievedSource,
)


class ExecutiveExperienceBuilder:
    """Packages existing advisory metadata into review-ready executive artifacts."""

    def build(
        self,
        *,
        intent: str,
        question: str,
        recommendations: list[str],
        risks: list[str],
        next_steps: list[str],
        sources: list[RetrievedSource],
        governance: EnterpriseGovernanceAssessment | None,
        topology: ArchitectureTopologySummary | None,
        decision_reasoning: list[ArchitectureDecisionReason],
        tradeoffs: list[ArchitectureTradeoffAnalysis],
        recommendation_confidence: list[RecommendationConfidenceIndicator],
        evidence_links: list[EvidenceLink],
        confidence: ConfidenceScore | None,
    ) -> ExecutiveExperienceSummary:
        executive_summary = self._executive_summary(
            intent=intent,
            recommendations=recommendations,
            risks=risks,
            governance=governance,
            confidence=confidence,
        )
        decision_brief = self._decision_brief(
            recommendations=recommendations,
            governance=governance,
            recommendation_confidence=recommendation_confidence,
            risks=risks,
        )
        sequence = self._implementation_sequence(
            recommendations=recommendations,
            next_steps=next_steps,
            governance=governance,
        )
        visualization = self._visualization(topology=topology, recommendations=recommendations)
        comparisons = list(governance.architecture_comparisons[:4]) if governance else []
        highlights = self._explainability_highlights(
            decision_reasoning=decision_reasoning,
            tradeoffs=tradeoffs,
            evidence_links=evidence_links,
            confidence=confidence,
            sources=sources,
        )
        artifacts = [
            ArchitectureReviewArtifact(
                title="Architecture review summary",
                markdown_summary=self._markdown_summary(
                    executive_summary=executive_summary,
                    decision_brief=decision_brief,
                    sequence=sequence,
                    visualization=visualization,
                    comparisons=comparisons,
                    risks=risks,
                    highlights=highlights,
                    sources=sources,
                ),
                json_summary={
                    "intent": intent,
                    "confidence": confidence.level if confidence else None,
                    "top_services": self._top_services(sources),
                    "recommendation_count": len(recommendations),
                    "risk_count": len(risks),
                    "comparison_count": len(comparisons),
                },
                review_checkpoints=self._review_checkpoints(intent=intent, governance=governance, risks=risks),
            )
        ]
        return ExecutiveExperienceSummary(
            executive_summary=executive_summary,
            decision_brief=decision_brief,
            implementation_sequence=sequence,
            architecture_visualization=visualization,
            comparison_summary=comparisons,
            explainability_highlights=highlights,
            review_artifacts=artifacts,
        )

    def _executive_summary(
        self,
        *,
        intent: str,
        recommendations: list[str],
        risks: list[str],
        governance: EnterpriseGovernanceAssessment | None,
        confidence: ConfidenceScore | None,
    ) -> str:
        if governance:
            business = governance.executive_summary.business_impact
            risk = governance.executive_summary.risk_summary
        else:
            business = "The advisory frames an OCI architecture path from the retrieved evidence and workload signals."
            risk = risks[0] if risks else "No elevated deterministic risk was detected from the available evidence."
        confidence_text = f" Overall confidence is {confidence.level} at {round(confidence.overall * 100)}%." if confidence else ""
        return (
            f"For this {intent.replace('_', ' ')} review, the immediate focus is to turn the top "
            f"{min(len(recommendations), 4)} recommendation(s) into sequenced implementation decisions. "
            f"{business} {risk}{confidence_text}"
        )

    def _decision_brief(
        self,
        *,
        recommendations: list[str],
        governance: EnterpriseGovernanceAssessment | None,
        recommendation_confidence: list[RecommendationConfidenceIndicator],
        risks: list[str],
    ) -> list[ExecutiveDecisionBrief]:
        priorities = {
            item.recommendation_index: item
            for item in (governance.recommendation_priorities if governance else [])
        }
        confidence_by_text = {item.recommendation: item for item in recommendation_confidence}
        briefs: list[ExecutiveDecisionBrief] = []
        for index, recommendation in enumerate(recommendations[:5]):
            priority = priorities.get(index)
            confidence = confidence_by_text.get(recommendation)
            brief_priority = priority.priority if priority else "recommended later" if index > 2 else "recommended immediately"
            briefs.append(
                ExecutiveDecisionBrief(
                    title=f"Decision {index + 1}",
                    summary=recommendation,
                    business_impact=(
                        priority.rationale
                        if priority
                        else "Clarifies the target OCI operating model and reduces ambiguity for delivery teams."
                    ),
                    risk_visibility=(
                        "; ".join(confidence.known_limitations[:2])
                        if confidence and confidence.known_limitations
                        else risks[index % len(risks)]
                        if risks
                        else "No specific elevated risk was detected from the available evidence."
                    ),
                    implementation_priority=brief_priority,
                )
            )
        return briefs

    def _implementation_sequence(
        self,
        *,
        recommendations: list[str],
        next_steps: list[str],
        governance: EnterpriseGovernanceAssessment | None,
    ) -> list[ImplementationSequenceItem]:
        immediate = [item for item in (governance.recommendation_priorities if governance else []) if "immediate" in item.priority]
        later = [item for item in (governance.recommendation_priorities if governance else []) if "later" in item.priority]
        return [
            ImplementationSequenceItem(
                phase="1. Architecture review",
                objective="Confirm the target design, assumptions, governance posture, and evidence gaps.",
                actions=[item.rationale for item in immediate[:3]] or recommendations[:2],
                exit_criteria=[
                    "Decision owner accepts recommendation priority.",
                    "Open risks have named mitigations or follow-up owners.",
                ],
            ),
            ImplementationSequenceItem(
                phase="2. Controlled implementation",
                objective="Implement the selected OCI services with observability, security controls, and rollback criteria.",
                actions=next_steps[:3] or recommendations[2:5],
                exit_criteria=[
                    "Runtime health, retrieval health, and fallback checks pass.",
                    "Deployment runbook and recovery path are validated.",
                ],
            ),
            ImplementationSequenceItem(
                phase="3. Optimization and scale",
                objective="Tune cost, resilience, operations, and release-refresh behavior after the baseline is stable.",
                actions=[item.rationale for item in later[:3]] or next_steps[3:6],
                exit_criteria=[
                    "Cost, reliability, and governance metrics are reviewed.",
                    "Post-implementation findings are fed back into the knowledge corpus or evals.",
                ],
            ),
        ]

    def _visualization(
        self,
        *,
        topology: ArchitectureTopologySummary | None,
        recommendations: list[str],
    ) -> ArchitectureVisualizationSummary | None:
        if topology is None:
            return None
        dependency_summary = [
            f"{item.from_node} -> {item.to_node}: {item.relationship}"
            for item in topology.service_dependencies[:8]
        ]
        migration_flow = [
            "Assess source-state dependencies and coexistence windows.",
            "Build OCI landing/runtime foundation and validate observability.",
            "Migrate by wave with rollback gates and release-readiness checks.",
        ]
        if not any("migration" in recommendation.lower() for recommendation in recommendations):
            migration_flow = [
                "Confirm workload criticality and architecture decision owners.",
                "Deploy the baseline topology with observable service boundaries.",
                "Tune resilience, cost, and governance controls after validation.",
            ]
        return ArchitectureVisualizationSummary(
            topology_summary=topology.topology_summary,
            dependency_summary=dependency_summary,
            deployment_view=topology.deployment_topology,
            ha_dr_view=topology.ha_dr_topology,
            migration_flow=migration_flow,
            mermaid_flow=topology.mermaid_flow,
        )

    def _explainability_highlights(
        self,
        *,
        decision_reasoning: list[ArchitectureDecisionReason],
        tradeoffs: list[ArchitectureTradeoffAnalysis],
        evidence_links: list[EvidenceLink],
        confidence: ConfidenceScore | None,
        sources: list[RetrievedSource],
    ) -> list[str]:
        highlights: list[str] = []
        if decision_reasoning:
            first = decision_reasoning[0]
            highlights.append(f"Service rationale: {first.why_chosen}")
        if tradeoffs:
            first_tradeoff = tradeoffs[0]
            highlights.append(
                f"Tradeoff: {first_tradeoff.dimension} favors {first_tradeoff.decision}; risk is {first_tradeoff.cost_or_risk}"
            )
        if evidence_links:
            highlights.append(
                f"Grounding: {len(evidence_links)} recommendation-to-evidence link(s) connect advice to retrieved chunks."
            )
        if confidence:
            highlights.append(
                f"Confidence: {confidence.level} overall with retrieval {round(confidence.retrieval * 100)}% and citation coverage {round(confidence.citation_coverage * 100)}%."
            )
        top_services = self._top_services(sources)
        if top_services:
            highlights.append(f"OCI evidence focus: {', '.join(top_services[:5])}.")
        return highlights[:6]

    def _review_checkpoints(
        self,
        *,
        intent: str,
        governance: EnterpriseGovernanceAssessment | None,
        risks: list[str],
    ) -> list[str]:
        checkpoints = [
            "Confirm decision owner, target environment, and implementation phase.",
            "Validate cited OCI evidence and any release-awareness caveats.",
            "Confirm monitoring, logging, rollback, and operating ownership before promotion.",
        ]
        if governance and governance.enterprise_review_findings:
            checkpoints.extend(f"{item.check}: {item.mitigation}" for item in governance.enterprise_review_findings[:3])
        if "migration" in intent:
            checkpoints.append("Confirm coexistence, migration wave sequencing, and rollback windows.")
        if risks:
            checkpoints.append("Review risk mitigations against the highest-severity open findings.")
        return checkpoints[:7]

    def _markdown_summary(
        self,
        *,
        executive_summary: str,
        decision_brief: list[ExecutiveDecisionBrief],
        sequence: list[ImplementationSequenceItem],
        visualization: ArchitectureVisualizationSummary | None,
        comparisons: list[ArchitectureComparison],
        risks: list[str],
        highlights: list[str],
        sources: list[RetrievedSource],
    ) -> str:
        lines = [
            "# Architecture Review Summary",
            "",
            "## Executive Summary",
            executive_summary,
            "",
            "## Priority Decisions",
        ]
        for item in decision_brief:
            lines.extend(
                [
                    f"- **{item.implementation_priority}:** {item.summary}",
                    f"  - Impact: {item.business_impact}",
                    f"  - Risk: {item.risk_visibility}",
                ]
            )
        lines.extend(["", "## Implementation Sequence"])
        for item in sequence:
            lines.append(f"- **{item.phase}:** {item.objective}")
            for action in item.actions[:3]:
                lines.append(f"  - {action}")
        if visualization:
            lines.extend(
                [
                    "",
                    "## Architecture View",
                    f"- Topology: {visualization.topology_summary}",
                    f"- Deployment: {visualization.deployment_view}",
                    f"- HA/DR: {visualization.ha_dr_view}",
                ]
            )
        if comparisons:
            lines.extend(["", "## Decision Comparisons"])
            for comparison in comparisons[:3]:
                lines.append(
                    f"- **{comparison.decision}:** prefer {comparison.preferred_option}; "
                    f"complexity: {comparison.operational_complexity}; cost: {comparison.cost_implications}"
                )
        lines.extend(["", "## Risks"])
        for risk in risks[:5]:
            lines.append(f"- {risk}")
        lines.extend(["", "## Explainability"])
        for highlight in highlights:
            lines.append(f"- {highlight}")
        lines.extend(["", "## Evidence"])
        for source in sources[:6]:
            label = source.service or source.service_domain or source.source_type
            lines.append(f"- {source.title} ({label})")
        return "\n".join(lines).strip()

    def _top_services(self, sources: list[RetrievedSource]) -> list[str]:
        services: list[str] = []
        for source in sources:
            if source.service and source.service not in services:
                services.append(source.service)
        return services
