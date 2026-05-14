from oci_arch_studio_backend.models.architecture import RetrievedSource


class PlaceholderRetriever:
    """Async-ready retrieval boundary for the future RAG implementation."""

    async def retrieve(self, question: str) -> list[RetrievedSource]:
        return [
            RetrievedSource(
                title="OCI Architecture Center",
                source_type="placeholder",
                url="https://docs.oracle.com/en/solutions/",
                summary=(
                    "Use OCI reference architectures and service documentation "
                    "as grounding material for architecture recommendations."
                ),
            ),
            RetrievedSource(
                title="OCI Well-Architected Guidance",
                source_type="placeholder",
                url="https://docs.oracle.com/iaas/Content/cloud-adoption-framework/well-architected-framework.htm",
                summary=(
                    "Review availability, security, performance, operations, "
                    "and cost considerations before finalizing an OCI design."
                ),
            ),
        ]
