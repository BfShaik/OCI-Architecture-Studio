import pytest

from oci_arch_studio_backend.services.embeddings import (
    FallbackEmbedder,
    LocalHashingEmbedder,
    OciGenerativeAiEmbedder,
    OciGenerativeAiEmbeddingConfig,
)


def test_oci_embedding_dimension_validation() -> None:
    embedder = OciGenerativeAiEmbedder(
        OciGenerativeAiEmbeddingConfig(
            region="us-ashburn-1",
            profile="DEFAULT",
            auth_mode="config_file",
            compartment_id="ocid1.compartment.oc1..example",
            model_id="cohere.embed-english-v3.0",
            expected_dimensions=3,
        )
    )

    embedder._validate_vector([0.1, 0.2, 0.3])  # noqa: SLF001 - direct validation regression.
    with pytest.raises(RuntimeError, match="dimension mismatch"):
        embedder._validate_vector([0.1, 0.2])  # noqa: SLF001 - direct validation regression.


def test_oci_embedding_request_includes_dimensions_and_input_type(monkeypatch) -> None:
    captured = {}

    class FakeServingMode:
        def __init__(self, model_id: str) -> None:
            self.model_id = model_id

    class FakeDetails:
        def __init__(self, **kwargs) -> None:
            self.__dict__.update(kwargs)
            captured["details"] = self

    class FakeClient:
        def embed_text(self, details):
            captured["sent_details"] = details
            return type("Response", (), {"data": type("Data", (), {"embeddings": [[0.1, 0.2, 0.3]]})()})()

    embedder = OciGenerativeAiEmbedder(
        OciGenerativeAiEmbeddingConfig(
            region="us-ashburn-1",
            profile="DEFAULT",
            auth_mode="config_file",
            compartment_id="ocid1.compartment.oc1..example",
            model_id="cohere.embed-v4.0",
            expected_dimensions=3,
            input_type="SEARCH_QUERY",
        )
    )
    fake_oci = type(
        "FakeOci",
        (),
        {
            "generative_ai_inference": type(
                "Inference",
                (),
                {
                    "models": type(
                        "Models",
                        (),
                        {
                            "OnDemandServingMode": FakeServingMode,
                            "EmbedTextDetails": FakeDetails,
                        },
                    )
                },
            )
        },
    )
    monkeypatch.setitem(__import__("sys").modules, "oci", fake_oci)
    embedder._client = FakeClient()  # noqa: SLF001 - direct request-shape regression.

    vector = embedder.embed("How should I design OCI retrieval?")

    details = captured["sent_details"]
    assert len(vector) == 3
    assert details.output_dimensions == 3
    assert details.input_type == "SEARCH_QUERY"
    assert details.serving_mode.model_id == "cohere.embed-v4.0"


def test_fallback_embedder_returns_local_vector_when_primary_fails() -> None:
    class FailingEmbedder:
        @property
        def model_name(self) -> str:
            return "failing-primary"

        def embed(self, text: str) -> list[float]:
            raise RuntimeError("simulated embedding outage")

    embedder = FallbackEmbedder(
        primary=FailingEmbedder(),
        fallback=LocalHashingEmbedder(dimensions=8),
    )

    vector = embedder.embed("OCI Load Balancer")
    diagnostics = embedder.diagnostics()

    assert len(vector) == 8
    assert diagnostics["fallback_count"] == 1
    assert "simulated embedding outage" in diagnostics["last_error"]
