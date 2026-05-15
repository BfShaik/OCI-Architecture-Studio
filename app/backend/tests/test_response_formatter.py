from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.response_formatter import build_section_citations


def test_section_citations_track_chunk_document_and_category() -> None:
    citations = build_section_citations(
        [
            RetrievedSource(
                chunk_id="logging::1",
                title="OCI Logging Overview",
                source_type="oci_doc",
                service="Logging",
                service_domain="observability",
                service_category="observability",
                summary="OCI Logging captures service and application logs.",
            )
        ]
    )

    observability = next(item for item in citations if item.section == "Observability")

    assert observability.sources[0].chunk_id == "logging::1"
    assert observability.sources[0].source_document == "OCI Logging Overview"
    assert observability.sources[0].oci_service_category == "observability"
