from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
)
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
    ) -> None:
        self.retriever = retriever
        self.classifier = classifier or IntentClassifier()
        self.release_store = release_store

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

        return ArchitectureReviewResponse(
            intent=profile.intent.value,
            prompt_template=profile.prompt_template,
            answer=(
                f"Intent: {profile.intent.value}. {context_note} Use the "
                f"{profile.prompt_template} template to focus the review on "
                f"{profile.focus}."
            ),
            recommendations=list(profile.recommendations),
            assumptions=list(profile.assumptions),
            risks=list(profile.risks),
            citations=sources,
            next_steps=list(profile.next_steps),
        )
