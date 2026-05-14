from oci_arch_studio_backend.models.architecture import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
)
from oci_arch_studio_backend.services.intents import (
    IntentClassifier,
    get_intent_profile,
)
from oci_arch_studio_backend.services.retrieval import OciKnowledgeRetriever


class ArchitectureReviewOrchestrator:
    """Coordinates intent classification, retrieval, and response shaping."""

    def __init__(
        self,
        retriever: OciKnowledgeRetriever,
        classifier: IntentClassifier | None = None,
    ) -> None:
        self.retriever = retriever
        self.classifier = classifier or IntentClassifier()

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

        context_note = (
            f"Retrieved {len(sources)} relevant OCI knowledge chunks from "
            f"{len(source_titles)} source document(s): {', '.join(source_titles)}."
            if has_index
            else sources[0].summary
        )

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
