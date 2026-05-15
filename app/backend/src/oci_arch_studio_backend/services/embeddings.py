import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}", re.IGNORECASE)


class Embedder(Protocol):
    @property
    def model_name(self) -> str:
        ...

    def embed(self, text: str) -> list[float]:
        ...


class LocalHashingEmbedder:
    """Small deterministic embedder for the first local RAG slice.

    This is not intended to be a production semantic model. It gives the
    ingestion and retrieval flow a real vector boundary without requiring an
    external embeddings API during the foundation phase.
    """

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    @property
    def model_name(self) -> str:
        return f"local-hashing-v1-{self.dimensions}"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = TOKEN_PATTERN.findall(text.lower())

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        return normalize(vector)


@dataclass(frozen=True)
class OciGenerativeAiEmbeddingConfig:
    region: str | None
    profile: str
    auth_mode: str
    compartment_id: str
    model_id: str
    endpoint: str | None = None
    expected_dimensions: int | None = None


class OciGenerativeAiEmbedder:
    """OCI Generative AI embedding adapter.

    The adapter is intentionally thin so local development and tests can keep
    using deterministic embeddings. It is activated only when explicitly
    configured through `EMBEDDING_PROVIDER=oci_genai`.
    """

    def __init__(self, config: OciGenerativeAiEmbeddingConfig) -> None:
        self.config = config
        self._client = None

    @property
    def model_name(self) -> str:
        return self.config.model_id

    def embed(self, text: str) -> list[float]:
        client = self._get_client()
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required for OCI Generative AI embeddings.") from exc

        serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=self.config.model_id,
        )
        details = oci.generative_ai_inference.models.EmbedTextDetails(
            compartment_id=self.config.compartment_id,
            serving_mode=serving_mode,
            inputs=[text],
            truncate="END",
        )
        response = client.embed_text(details)
        embeddings = getattr(response.data, "embeddings", None) or []
        if not embeddings:
            raise RuntimeError("OCI Generative AI returned no embedding.")
        vector = [float(value) for value in embeddings[0]]
        self._validate_vector(vector)
        return normalize(vector)

    def _validate_vector(self, vector: list[float]) -> None:
        if not vector:
            raise RuntimeError("OCI Generative AI returned an empty embedding.")
        if self.config.expected_dimensions is not None and len(vector) != self.config.expected_dimensions:
            raise RuntimeError(
                "OCI Generative AI embedding dimension mismatch: "
                f"expected {self.config.expected_dimensions}, got {len(vector)}."
            )

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required for OCI Generative AI embeddings.") from exc

        if self.config.auth_mode == "instance_principal":
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            client_config = {"region": self.config.region} if self.config.region else {}
            self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                config=client_config,
                signer=signer,
                service_endpoint=self.config.endpoint,
            )
        elif self.config.auth_mode == "resource_principal":
            signer = oci.auth.signers.get_resource_principals_signer()
            client_config = {"region": self.config.region} if self.config.region else {}
            self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                config=client_config,
                signer=signer,
                service_endpoint=self.config.endpoint,
            )
        else:
            client_config = oci.config.from_file(profile_name=self.config.profile)
            if self.config.region:
                client_config["region"] = self.config.region
            self._client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                config=client_config,
                service_endpoint=self.config.endpoint,
            )
        return self._client


class FallbackEmbedder:
    """Wraps an optional primary embedder and falls back to deterministic embeddings."""

    def __init__(
        self,
        *,
        primary: Embedder | None,
        fallback: Embedder | None = None,
        activation_error: str | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback or LocalHashingEmbedder()
        self.activation_error = activation_error
        self.last_error: str | None = activation_error
        self.fallback_count = 0

    @property
    def model_name(self) -> str:
        if self.primary is None:
            return f"{self.fallback.model_name}-fallback"
        return f"{self.primary.model_name}-with-{self.fallback.model_name}-fallback"

    def embed(self, text: str) -> list[float]:
        if self.primary is None:
            self.fallback_count += 1
            return self.fallback.embed(text)
        try:
            return self.primary.embed(text)
        except Exception as exc:  # noqa: BLE001 - embedding fallback preserves retrieval availability.
            self.last_error = f"{type(exc).__name__}: {exc}"
            self.fallback_count += 1
            return self.fallback.embed(text)

    def diagnostics(self) -> dict[str, object]:
        return {
            "primary_model": self.primary.model_name if self.primary is not None else None,
            "fallback_model": self.fallback.model_name,
            "fallback_enabled": True,
            "fallback_count": self.fallback_count,
            "last_error": self.last_error,
            "activation_error": self.activation_error,
        }


def normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(left_value * right_value for left_value, right_value in zip(left, right))
