from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
)
from oci_arch_studio_backend.services.advisory_metrics import advisory_quality_metrics
from oci_arch_studio_backend.services.advisory_quality import AdvisoryQualityAnalyzer
from oci_arch_studio_backend.services.intents import (
    IntentClassifier,
    get_intent_profile,
)
from oci_arch_studio_backend.services.releases import ReleaseSnapshotStore
from oci_arch_studio_backend.services.retrieval import OciKnowledgeRetriever


class ArchitectureReviewOrchestrator:
    """Coordinates intent classification, retrieval, and response shaping."""

    def __init__(
        self,
        retriever: OciKnowledgeRetriever,
        classifier: IntentClassifier | None = None,
        release_store: ReleaseSnapshotStore | None = None,
        quality_analyzer: AdvisoryQualityAnalyzer | None = None,
    ) -> None:
        self.retriever = retriever
        self.classifier = classifier or IntentClassifier()
        self.release_store = release_store
        self.quality_analyzer = quality_analyzer or AdvisoryQualityAnalyzer()

    async def review(
        self,
        request: ArchitectureReviewRequest,
    ) -> ArchitectureReviewResponse:
        classifier_text = " ".join(
            part for part in (request.question, request.workload_context) if part
        )
        intent = self.classifier.classify(classifier_text)
        profile = get_intent_profile(intent)

        sources = await self.retriever.retrieve(
            request.question,
            intent_profile=profile,
        )
        source_titles = sorted({source.title for source in sources})
        has_index = all(source.source_type != "missing_index" for source in sources)
        stale_sources = [source for source in sources if source.is_stale]
        quality = self.quality_analyzer.assess(
            question=request.question,
            profile=profile,
            base_recommendations=list(profile.recommendations),
            sources=sources,
            release_store=self.release_store,
        )

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
            warnings=quality.quality_warnings,
        )

        return ArchitectureReviewResponse(
            intent=profile.intent.value,
            prompt_template=profile.prompt_template,
            answer=(
                f"Intent: {profile.intent.value}. {context_note} Use the "
                f"{profile.prompt_template} template to focus the review on "
                f"{profile.focus}."
            ),
            recommendations=quality.recommendations,
            assumptions=list(profile.assumptions),
            risks=list(profile.risks),
            citations=sources,
            evidence_links=quality.evidence_links,
            confidence=quality.confidence,
            quality_warnings=quality.quality_warnings,
            unsupported_claims=quality.unsupported_claims,
            not_enough_evidence=quality.not_enough_evidence,
            low_confidence=quality.low_confidence,
            next_steps=list(profile.next_steps),
        )
