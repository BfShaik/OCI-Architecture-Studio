from oci_arch_studio_backend.models.architecture import (
    ArchitectureReasoningTrace,
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    ArchitectureTradeoffAnalysis,
    RecommendationConfidenceIndicator,
)
from oci_arch_studio_backend.services.advisory_metrics import advisory_quality_metrics
from oci_arch_studio_backend.services.advisory_quality import AdvisoryQualityAnalyzer
from oci_arch_studio_backend.services.architecture_consistency import ArchitectureConsistencyValidator
from oci_arch_studio_backend.services.architecture_reasoning import ArchitectureDecisionReasoner
from oci_arch_studio_backend.services.architecture_reasoning_engine import ArchitectureReasoningEngine
from oci_arch_studio_backend.services.architecture_topology import ArchitectureTopologyBuilder
from oci_arch_studio_backend.services.enterprise_governance import EnterpriseGovernanceAdvisor
from oci_arch_studio_backend.services.executive_experience import ExecutiveExperienceBuilder
from oci_arch_studio_backend.services.intents import (
    IntentClassifier,
    get_intent_profile,
)
from oci_arch_studio_backend.services.operational import operational_metrics
from oci_arch_studio_backend.services.optimization_advisor import OptimizationAdvisor
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore
from oci_arch_studio_backend.services.response_formatter import build_section_citations
from oci_arch_studio_backend.services.retrieval import OciKnowledgeRetriever
from oci_arch_studio_backend.services.synthesis import (
    AdvisorySynthesizer,
    DeterministicAdvisorySynthesizer,
    SynthesisRequest,
)
from oci_arch_studio_backend.services.supervised_orchestration import (
    SupervisedAgentOrchestrator,
)


class ArchitectureReviewOrchestrator:
    """Coordinates intent classification, retrieval, and response shaping."""

    def __init__(
        self,
        retriever: OciKnowledgeRetriever,
        classifier: IntentClassifier | None = None,
        release_store: ReleaseSnapshotStore | None = None,
        quality_analyzer: AdvisoryQualityAnalyzer | None = None,
        synthesizer: AdvisorySynthesizer | None = None,
        agent_orchestrator: SupervisedAgentOrchestrator | None = None,
        consistency_validator: ArchitectureConsistencyValidator | None = None,
        decision_reasoner: ArchitectureDecisionReasoner | None = None,
        reasoning_engine: ArchitectureReasoningEngine | None = None,
        governance_advisor: EnterpriseGovernanceAdvisor | None = None,
        topology_builder: ArchitectureTopologyBuilder | None = None,
        executive_experience_builder: ExecutiveExperienceBuilder | None = None,
        optimization_advisor: OptimizationAdvisor | None = None,
        synthesis_debug_enabled: bool = False,
    ) -> None:
        self.retriever = retriever
        self.classifier = classifier or IntentClassifier()
        self.release_store = release_store
        self.quality_analyzer = quality_analyzer or AdvisoryQualityAnalyzer()
        self.synthesizer = synthesizer or DeterministicAdvisorySynthesizer()
        self.agent_orchestrator = agent_orchestrator or SupervisedAgentOrchestrator()
        self.consistency_validator = consistency_validator or ArchitectureConsistencyValidator()
        self.decision_reasoner = decision_reasoner or ArchitectureDecisionReasoner()
        self.reasoning_engine = reasoning_engine or ArchitectureReasoningEngine()
        self.governance_advisor = governance_advisor or EnterpriseGovernanceAdvisor()
        self.topology_builder = topology_builder or ArchitectureTopologyBuilder()
        self.executive_experience_builder = executive_experience_builder or ExecutiveExperienceBuilder()
        self.optimization_advisor = optimization_advisor or OptimizationAdvisor()
        self.synthesis_debug_enabled = synthesis_debug_enabled

    async def review(
        self,
        request: ArchitectureReviewRequest,
    ) -> ArchitectureReviewResponse:
        operational_started_at = operational_metrics.start()
        classifier_text = " ".join(
            part for part in (request.question, request.workload_context) if part
        )
        intent = self.classifier.classify(classifier_text)
        profile = get_intent_profile(intent)
        reasoning_terms = self.reasoning_engine.pre_retrieval_terms(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
        )
        release_context_terms = (
            self.release_store.retrieval_context_terms(request.question)
            if self.release_store is not None
            else []
        )
        retrieval_workload_context = " ".join(
            part
            for part in (
                request.workload_context,
                " ".join(reasoning_terms) if reasoning_terms else None,
                " ".join(release_context_terms) if release_context_terms else None,
            )
            if part
        ) or None

        sources = await self.retriever.retrieve(
            request.question,
            intent_profile=profile,
            workload_context=retrieval_workload_context,
            debug_enabled=request.retrieval_debug,
        )
        source_titles = sorted({source.title for source in sources})
        has_index = all(source.source_type != "missing_index" for source in sources)
        stale_sources = [source for source in sources if source.is_stale]

        context_note = (
            f"Retrieved {len(sources)} relevant OCI knowledge chunks from "
            f"{len(source_titles)} source document(s): {', '.join(source_titles)}."
            if has_index
            else sources[0].summary
        )
        if has_index and stale_sources:
            context_note += (
                f" {len(stale_sources)} retrieved source(s) may be stale or missing freshness metadata; "
                "verify current release context before relying on affected guidance."
            )
        if profile.intent.value == "release_awareness":
            context_note += (
                " Release-aware guidance must compare the local knowledge snapshot against "
                "approved OCI release snapshots before declaring current impact."
            )
        if self.release_store is not None:
            release_note = self.release_store.freshness_note(profile.intent, request.question)
            if release_note:
                context_note += f" {release_note}"

        orchestration_plan = self.agent_orchestrator.plan(
            question=request.question,
            profile=profile,
            sources=sources,
            context_note=context_note,
        )

        synthesis = self.synthesizer.synthesize(
            SynthesisRequest(
                question=request.question,
                workload_context=request.workload_context,
                profile=profile,
                sources=sources,
                context_note=orchestration_plan.context_note,
                debug_enabled=bool(request.synthesis_debug or self.synthesis_debug_enabled),
            )
        )
        optimization_plan = self.optimization_advisor.build(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
            sources=sources,
            base_recommendations=synthesis.recommendations,
        )
        enriched_recommendations = self._merge_recommendations(
            synthesis.recommendations,
            optimization_plan.recommendation_additions,
        )
        quality = self.quality_analyzer.assess(
            question=request.question,
            profile=profile,
            base_recommendations=enriched_recommendations,
            sources=sources,
            release_store=self.release_store,
        )
        if quality.not_enough_evidence:
            context_note += (
                " Not enough evidence is available for a final design; treat the response as "
                "a provisional advisory and gather the missing workload or source context."
            )
        if quality.unsupported_claims:
            context_note += (
                " The prompt contains requested capabilities that are not supported by the "
                "retrieved OCI evidence; they are flagged instead of accepted as valid OCI services."
            )
        decision_reasoning = self.decision_reasoner.build(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
            recommendations=quality.recommendations,
            evidence_links=quality.evidence_links,
            sources=sources,
        )
        reasoning_result = self.reasoning_engine.analyze(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
            sources=sources,
            recommendations=quality.recommendations,
            synthesis_provider=synthesis.provider,
        )
        consistency_findings = self.consistency_validator.validate(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
            answer=synthesis.answer,
            recommendations=quality.recommendations,
            sources=sources,
        )
        critique = self.agent_orchestrator.critique(
            synthesis=synthesis,
            quality=quality,
            sources=sources,
        )
        orchestration_warnings = [*orchestration_plan.warnings, *critique.warnings]
        consistency_warnings = [
            finding.message
            for finding in consistency_findings
            if finding.severity in {"warning", "error"}
        ]
        release_context = (
            self.release_store.impact_summary(request.question)
            if self.release_store is not None
            else None
        )
        temporal_context = (
            self.release_store.temporal_context(
                knowledge_snapshot_path=getattr(self.retriever.store, "index_path", None),
                question=request.question,
            )
            if self.release_store is not None
            else None
        )
        governance_assessment = self.governance_advisor.assess(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
            sources=sources,
            recommendations=quality.recommendations,
            decision_reasoning=decision_reasoning,
            reasoning_result=reasoning_result,
            consistency_findings=consistency_findings,
            release_context=release_context,
            temporal_context=temporal_context,
            confidence=quality.confidence,
            synthesis_provider=synthesis.provider,
            synthesis_fallback_used=synthesis.used_fallback,
            quality_warnings=[*quality.quality_warnings, *synthesis.warnings, *consistency_warnings],
            unsupported_claims=quality.unsupported_claims,
        )
        architecture_topology = self.topology_builder.build(
            question=request.question,
            workload_context=request.workload_context,
            profile=profile,
            sources=sources,
            recommendations=quality.recommendations,
        )
        architecture_tradeoffs = [
            ArchitectureTradeoffAnalysis(
                dimension=tradeoff.dimension,
                decision=tradeoff.decision,
                benefit=tradeoff.benefit,
                cost_or_risk=tradeoff.cost_or_risk,
                guidance=tradeoff.guidance,
                source_chunk_ids=list(tradeoff.source_chunk_ids),
            )
            for tradeoff in reasoning_result.tradeoffs
        ]
        recommendation_confidence = [
            RecommendationConfidenceIndicator(
                recommendation=item.recommendation,
                score=item.score,
                level=item.level,
                reasoning_basis=item.reasoning_basis,
                source_chunk_ids=list(item.source_chunk_ids),
                known_limitations=list(item.known_limitations),
                assumptions=list(item.assumptions),
            )
            for item in reasoning_result.recommendation_confidence
        ]
        executive_experience = self.executive_experience_builder.build(
            intent=profile.intent.value,
            question=request.question,
            recommendations=quality.recommendations,
            risks=synthesis.risks,
            next_steps=synthesis.next_steps,
            sources=sources,
            governance=governance_assessment,
            topology=architecture_topology,
            decision_reasoning=decision_reasoning,
            tradeoffs=architecture_tradeoffs,
            recommendation_confidence=recommendation_confidence,
            evidence_links=quality.evidence_links,
            confidence=quality.confidence,
        )

        advisory_quality_metrics.record(
            intent=profile.intent.value,
            confidence_level=quality.confidence.level,
            overall_confidence=quality.confidence.overall,
            citation_coverage=quality.citation_coverage,
            evidence_support=quality.evidence_support,
            low_confidence=quality.low_confidence,
            not_enough_evidence=quality.not_enough_evidence,
            unsupported_claims=quality.unsupported_claims,
            stale_evidence_count=len(stale_sources),
            synthesis_provider=synthesis.provider,
            synthesis_fallback_used=synthesis.used_fallback,
            synthesis_latency_ms=synthesis.latency_ms,
            orchestration_mode=orchestration_plan.mode,
            active_agents=orchestration_plan.active_agents,
            routing_decision=orchestration_plan.routing_decision,
            aggregation_decision=orchestration_plan.aggregation_decision,
            critic_warnings=critique.warnings,
            warnings=[*quality.quality_warnings, *synthesis.warnings, *orchestration_warnings, *consistency_warnings],
        )

        response = ArchitectureReviewResponse(
            intent=profile.intent.value,
            prompt_template=profile.prompt_template,
            orchestration_mode=orchestration_plan.mode,
            active_agents=orchestration_plan.active_agents,
            routing_decision=orchestration_plan.routing_decision,
            agent_trace=[*orchestration_plan.traces, *critique.traces],
            agent_contributions=orchestration_plan.contributions,
            aggregation_decision=orchestration_plan.aggregation_decision,
            critic_findings=critique.findings,
            orchestration_warnings=orchestration_warnings,
            synthesis_provider=synthesis.provider,
            synthesis_model=synthesis.model,
            synthesis_warnings=synthesis.warnings,
            synthesis_fallback_used=synthesis.used_fallback,
            synthesis_quality=synthesis.quality,
            synthesis_debug=synthesis.debug,
            decision_reasoning=decision_reasoning,
            reasoning_trace=ArchitectureReasoningTrace(
                profile=reasoning_result.profile.name,
                heuristics_triggered=list(reasoning_result.heuristics_triggered),
                pattern_hints=list(reasoning_result.pattern_hints),
                retrieval_terms=list(reasoning_result.retrieval_terms),
                service_priorities=list(reasoning_result.service_priorities),
                risk_emphasis=list(reasoning_result.risk_emphasis),
                synthesis_provider=synthesis.provider,
            ),
            architecture_tradeoffs=[
                *architecture_tradeoffs,
            ],
            recommendation_confidence=[*recommendation_confidence],
            consistency_findings=consistency_findings,
            release_context=release_context,
            knowledge_temporal_context=temporal_context,
            enterprise_governance=governance_assessment,
            architecture_topology=architecture_topology,
            executive_experience=executive_experience,
            optimization_plan=optimization_plan,
            answer=synthesis.answer if not quality.not_enough_evidence else f"{synthesis.answer} {context_note}",
            recommendations=quality.recommendations,
            assumptions=synthesis.assumptions,
            risks=synthesis.risks,
            citations=sources,
            section_citations=build_section_citations(sources),
            retrieval_debug=self.retriever.last_debug_trace,
            evidence_links=quality.evidence_links,
            confidence=quality.confidence,
            quality_warnings=[*quality.quality_warnings, *synthesis.warnings, *consistency_warnings],
            unsupported_claims=quality.unsupported_claims,
            not_enough_evidence=quality.not_enough_evidence,
            low_confidence=quality.low_confidence,
            next_steps=synthesis.next_steps,
        )
        operational_metrics.record_response(
            started_at=operational_started_at,
            response=response.model_dump(),
        )
        return response

    def _merge_recommendations(self, base: list[str], additions: list[str]) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for recommendation in (*base, *additions):
            normalized = " ".join(recommendation.lower().split())
            if normalized in seen:
                continue
            seen.add(normalized)
            merged.append(recommendation)
        return merged[:10]
