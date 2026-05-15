import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from oci_arch_studio_backend.services.embeddings import cosine_similarity


@dataclass(frozen=True)
class VectorChunk:
    id: str
    title: str
    url: str | None
    source_type: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VectorSearchFilters:
    intent: str | None = None
    service_domain: str | None = None
    service_domains: tuple[str, ...] = ()
    services: tuple[str, ...] = ()
    architecture_patterns: tuple[str, ...] = ()
    min_freshness_score: float | None = None
    trust_level: str | None = None
    release_aware: bool = False


class VectorStore(Protocol):
    @property
    def exists(self) -> bool:
        ...

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        filters: VectorSearchFilters | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        ...

    def health(self) -> dict[str, object]:
        ...


class JsonVectorStore:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        self._chunks: list[VectorChunk] | None = None

    @property
    def exists(self) -> bool:
        return self.index_path.exists()

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        intent: str | None = None,
        filters: VectorSearchFilters | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        filters = filters or VectorSearchFilters(intent=intent)
        chunks = self._load_chunks()
        candidates = [chunk for chunk in chunks if self._matches_filters(chunk, filters)]
        scored = [
            (chunk, self._rank_score(chunk, cosine_similarity(query_embedding, chunk.embedding), filters))
            for chunk in candidates
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def health(self) -> dict[str, object]:
        chunks = self._load_chunks()
        services = sorted(
            {
                str(chunk.metadata.get("service"))
                for chunk in chunks
                if chunk.metadata.get("service")
            }
        )
        domains = sorted(
            {
                str(chunk.metadata.get("service_domain"))
                for chunk in chunks
                if chunk.metadata.get("service_domain")
            }
        )
        stale_count = sum(
            1
            for chunk in chunks
            if isinstance(chunk.metadata.get("freshness_score"), int | float)
            and float(chunk.metadata["freshness_score"]) < 0.5
        )
        return {
            "provider": "local_json",
            "exists": self.exists,
            "chunk_count": len(chunks),
            "index_path": str(self.index_path),
            "service_count": len(services),
            "service_domain_count": len(domains),
            "services": services[:20],
            "service_domains": domains,
            "low_freshness_chunk_count": stale_count,
        }

    def _matches_filters(self, chunk: VectorChunk, filters: VectorSearchFilters) -> bool:
        metadata = chunk.metadata
        if filters.service_domain and metadata.get("service_domain") != filters.service_domain:
            return False
        if filters.trust_level and metadata.get("trust_level") != filters.trust_level:
            return False
        freshness_score = metadata.get("freshness_score")
        if filters.min_freshness_score is not None and isinstance(freshness_score, int | float):
            return float(freshness_score) >= filters.min_freshness_score
        return True

    def _rank_score(self, chunk: VectorChunk, similarity: float, filters: VectorSearchFilters) -> float:
        metadata = chunk.metadata
        score = similarity
        service = str(metadata.get("service", "")).lower()
        domain = str(metadata.get("service_domain", "")).lower()
        patterns = {str(pattern).lower() for pattern in metadata.get("architecture_patterns", [])}
        if filters.intent and filters.intent in metadata.get("intent_tags", []):
            score += 0.08
        if domain and domain in {item.lower() for item in filters.service_domains}:
            score += 0.05
        if service and service in {item.lower() for item in filters.services}:
            score += 0.05
        if patterns.intersection({item.lower() for item in filters.architecture_patterns}):
            score += 0.04
        if metadata.get("trust_level") == "official":
            score += 0.03
        freshness_score = metadata.get("freshness_score")
        if isinstance(freshness_score, int | float):
            score += min(max(float(freshness_score), 0.0), 1.0) * 0.02
            if float(freshness_score) < 0.5:
                score -= 0.04
        if filters.release_aware and "release" in metadata.get("intent_tags", []):
            score += 0.04
        return score

    def _load_chunks(self) -> list[VectorChunk]:
        if self._chunks is not None:
            return self._chunks

        if not self.index_path.exists():
            self._chunks = []
            return self._chunks

        with self.index_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        self._chunks = [
            VectorChunk(
                id=chunk["id"],
                title=chunk["title"],
                url=chunk.get("url"),
                source_type=chunk.get("source_type", "oci_doc"),
                text=chunk["text"],
                embedding=chunk["embedding"],
                metadata=chunk.get("metadata", {}),
            )
            for chunk in payload.get("chunks", [])
        ]
        return self._chunks


@dataclass(frozen=True)
class OciObjectStorageVectorConfig:
    namespace: str
    bucket_name: str
    object_name: str
    region: str | None = None
    profile: str = "DEFAULT"
    auth_mode: str = "config_file"


class OciObjectStorageVectorStore(JsonVectorStore):
    """OCI-native vector manifest store for the first retrieval migration slice.

    Phase 1 stores the same citation-preserving vector manifest in OCI Object
    Storage. This keeps the validated local contract while preparing the
    migration path to Oracle AI Vector Search.
    """

    def __init__(self, config: OciObjectStorageVectorConfig) -> None:
        super().__init__(index_path=Path(f"oci://{config.bucket_name}/{config.object_name}"))
        self.config = config
        self._last_error: str | None = None

    @property
    def exists(self) -> bool:
        try:
            exists = bool(self._read_object_text())
            self._last_error = None
            return exists
        except Exception as exc:
            self._last_error = str(exc)
            return False

    def health(self) -> dict[str, object]:
        try:
            chunks = self._load_chunks()
            self._last_error = None
        except Exception as exc:
            chunks = []
            self._last_error = str(exc)
        services = sorted(
            {
                str(chunk.metadata.get("service"))
                for chunk in chunks
                if chunk.metadata.get("service")
            }
        )
        domains = sorted(
            {
                str(chunk.metadata.get("service_domain"))
                for chunk in chunks
                if chunk.metadata.get("service_domain")
            }
        )
        return {
            "provider": "oci_object_storage_vector_manifest",
            "exists": bool(chunks),
            "chunk_count": len(chunks),
            "namespace": self.config.namespace,
            "bucket": self.config.bucket_name,
            "object_name": self.config.object_name,
            "service_count": len(services),
            "service_domain_count": len(domains),
            "services": services[:20],
            "service_domains": domains,
            "last_error": self._last_error,
        }

    def _load_chunks(self) -> list[VectorChunk]:
        if self._chunks is not None:
            return self._chunks

        payload = json.loads(self._read_object_text())
        self._chunks = [
            VectorChunk(
                id=chunk["id"],
                title=chunk["title"],
                url=chunk.get("url"),
                source_type=chunk.get("source_type", "oci_doc"),
                text=chunk["text"],
                embedding=chunk["embedding"],
                metadata=chunk.get("metadata", {}),
            )
            for chunk in payload.get("chunks", [])
        ]
        return self._chunks

    def _read_object_text(self) -> str:
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required for OCI Object Storage vector retrieval.") from exc

        if self.config.auth_mode == "instance_principal":
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            client_config = {"region": self.config.region} if self.config.region else {}
            object_storage = oci.object_storage.ObjectStorageClient(client_config, signer=signer)
        else:
            client_config = oci.config.from_file(profile_name=self.config.profile)
            if self.config.region:
                client_config["region"] = self.config.region
            object_storage = oci.object_storage.ObjectStorageClient(client_config)

        response = object_storage.get_object(
            namespace_name=self.config.namespace,
            bucket_name=self.config.bucket_name,
            object_name=self.config.object_name,
        )
        return response.data.content.decode("utf-8")


@dataclass(frozen=True)
class OracleAiVectorSearchConfig:
    """Configuration for the future Oracle AI Vector Search read path.

    The first Sprint 2 slice keeps this adapter behind explicit configuration
    so local and staging behavior stay stable while the vector schema and DB
    connectivity are validated.
    """

    dsn: str | None = None
    username: str | None = None
    password: str | None = None
    table_name: str = "OCI_ARCHITECTURE_CHUNKS"
    embedding_column: str = "EMBEDDING"
    metadata_column: str = "METADATA_JSON"


class OracleAiVectorSearchStore:
    """Guarded Oracle AI Vector Search adapter skeleton.

    This class defines the production retrieval boundary without changing the
    default runtime. It intentionally refuses search until required DB inputs
    are present, which prevents accidental partial cutover.
    """

    def __init__(self, config: OracleAiVectorSearchConfig) -> None:
        self.config = config

    @property
    def exists(self) -> bool:
        return all((self.config.dsn, self.config.username, self.config.password))

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        filters: VectorSearchFilters | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        raise RuntimeError(
            "Oracle AI Vector Search retrieval is configured as a Phase 2 adapter boundary "
            "but is not enabled for reads yet. Use RETRIEVAL_PROVIDER=local_json or "
            "RETRIEVAL_PROVIDER=oci_object_storage until vector schema validation is complete."
        )

    def health(self) -> dict[str, object]:
        missing = [
            name
            for name, value in (
                ("OCI_VECTOR_DB_DSN", self.config.dsn),
                ("OCI_VECTOR_DB_USER", self.config.username),
                ("OCI_VECTOR_DB_PASSWORD", self.config.password),
            )
            if not value
        ]
        return {
            "provider": "oracle_ai_vector_search",
            "exists": self.exists,
            "read_enabled": False,
            "table_name": self.config.table_name,
            "embedding_column": self.config.embedding_column,
            "metadata_column": self.config.metadata_column,
            "missing_config": missing,
            "migration_phase": "phase_2_schema_validation",
        }
