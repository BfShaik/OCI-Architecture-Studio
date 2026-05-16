import json
import threading
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Protocol

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
    workload_types: tuple[str, ...] = ()
    domain_tags: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    min_freshness_score: float | None = None
    trust_level: str | None = None
    release_aware: bool = False

    def has_metadata_filters(self) -> bool:
        return bool(
            self.intent
            or self.service_domain
            or self.service_domains
            or self.services
            or self.architecture_patterns
            or self.workload_types
            or self.domain_tags
            or self.topics
            or self.min_freshness_score is not None
            or self.trust_level
            or self.release_aware
        )


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


class UnavailableVectorStore:
    def __init__(self, provider_name: str, reason: str, missing_config: list[str] | None = None) -> None:
        self.provider_name = provider_name
        self.reason = reason
        self.missing_config = missing_config or []

    @property
    def exists(self) -> bool:
        return False

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        filters: VectorSearchFilters | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        raise RuntimeError(self.reason)

    def health(self) -> dict[str, object]:
        return {
            "provider": self.provider_name,
            "exists": False,
            "read_enabled": False,
            "chunk_count": 0,
            "service_count": 0,
            "service_domain_count": 0,
            "missing_config": self.missing_config,
            "last_error": self.reason,
        }


class JsonVectorStore:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path
        self._chunks: list[VectorChunk] | None = None
        self._manifest_metadata: dict[str, object] | None = None

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
            **self._embedding_health(),
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
        if not _metadata_soft_match(metadata, filters):
            return False
        return True

    def _rank_score(self, chunk: VectorChunk, similarity: float, filters: VectorSearchFilters) -> float:
        metadata = chunk.metadata
        score = similarity
        service = str(metadata.get("service", "")).lower()
        domain = str(metadata.get("service_domain", "")).lower()
        patterns = {str(pattern).lower() for pattern in metadata.get("architecture_patterns", [])}
        workload_types = {str(workload).lower() for workload in metadata.get("workload_types", [])}
        domain_tags = {str(tag).lower() for tag in metadata.get("domain_tags", [])}
        topic = str(metadata.get("topic", "")).lower()
        if filters.intent and filters.intent in metadata.get("intent_tags", []):
            score += 0.08
        if domain and domain in {item.lower() for item in filters.service_domains}:
            score += 0.07
        if service and service in {item.lower() for item in filters.services}:
            score += 0.16
        if patterns.intersection({item.lower() for item in filters.architecture_patterns}):
            score += 0.04
        if workload_types.intersection({item.lower() for item in filters.workload_types}):
            score += 0.04
        if domain_tags.intersection({item.lower() for item in filters.domain_tags}):
            score += 0.03
        if topic and topic in {item.lower() for item in filters.topics}:
            score += 0.03
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

        self._manifest_metadata = self._extract_manifest_metadata(payload)
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

    def _embedding_health(self) -> dict[str, object]:
        metadata = self._manifest_metadata or {}
        return {
            "index_embedding_provider": metadata.get("embedding_provider"),
            "index_embedding_model": metadata.get("embedding_model"),
            "index_dimensions": metadata.get("dimensions"),
        }

    def _extract_manifest_metadata(self, payload: dict[str, object]) -> dict[str, object]:
        dimensions = payload.get("dimensions")
        chunks = payload.get("chunks", [])
        if dimensions is None and isinstance(chunks, list) and chunks:
            first_embedding = chunks[0].get("embedding") if isinstance(chunks[0], dict) else None
            if isinstance(first_embedding, list):
                dimensions = len(first_embedding)
        return {
            "embedding_provider": payload.get("embedding_provider"),
            "embedding_model": payload.get("embedding_model"),
            "dimensions": dimensions,
        }


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
        if self._chunks is not None:
            return True
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
            **self._embedding_health(),
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
        self._manifest_metadata = self._extract_manifest_metadata(payload)
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
    dsn: str | None = None
    username: str | None = None
    password: str | None = None
    wallet_location: str | None = None
    wallet_password: str | None = None
    table_name: str = "OCI_ARCHITECTURE_CHUNKS"
    index_name: str = "OCI_ARCH_CHUNKS_VEC_IDX"
    embedding_column: str = "EMBEDDING"
    metadata_column: str = "METADATA_JSON"
    dimensions: int = 256
    distance_metric: str = "COSINE"
    connect_timeout_seconds: int = 10


class OracleAiVectorSearchStore:
    """Oracle AI Vector Search provider.

    The provider uses Oracle Database vector search when explicitly configured.
    It stays optional so local development can keep using the JSON vector store.
    """

    def __init__(
        self,
        config: OracleAiVectorSearchConfig,
        connection_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.config = config
        self.connection_factory = connection_factory
        self._last_error: str | None = None
        self._last_query: dict[str, object] = {}
        self._pool: Any | None = None
        self._pool_lock = threading.Lock()

    @property
    def exists(self) -> bool:
        if not self._is_configured():
            return False
        try:
            self.validate_schema()
            self._last_error = None
            return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        filters: VectorSearchFilters | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        if not self._is_configured():
            raise RuntimeError("Oracle AI Vector Search is missing required database configuration.")
        self._validate_embedding(query_embedding)
        filters = filters or VectorSearchFilters()
        sql, binds = self._search_sql(top_k=top_k, filters=filters)
        binds["query_embedding"] = json.dumps(query_embedding)
        started_at = perf_counter()
        try:
            with self._connect() as connection:
                cursor = connection.cursor()
                self._set_search_input_sizes(cursor)
                cursor.execute(sql, binds)
                rows = cursor.fetchall()
                results = [self._row_to_result(row) for row in rows]
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            self._last_error = None
            self._last_query = {
                "latency_ms": latency_ms,
                "metadata_filters": self._filter_summary(filters),
                "top_k": top_k,
                "result_count": len(rows),
            }
            return results
        except Exception as exc:
            self._last_error = str(exc)
            raise

    def upsert_chunks(self, chunks: list[VectorChunk]) -> int:
        if not self._is_configured():
            raise RuntimeError("Oracle AI Vector Search is missing required database configuration.")
        if not chunks:
            return 0
        rows = [self._chunk_binds(chunk) for chunk in chunks]
        try:
            with self._connect() as connection:
                cursor = connection.cursor()
                self._set_upsert_input_sizes(cursor)
                cursor.executemany(self.upsert_sql(), rows)
                connection.commit()
            self._last_error = None
            return len(rows)
        except Exception as exc:
            self._last_error = str(exc)
            raise

    def create_schema(self) -> None:
        if not self._is_configured():
            raise RuntimeError("Oracle AI Vector Search is missing required database configuration.")
        try:
            with self._connect() as connection:
                cursor = connection.cursor()
                for statement in self.schema_sql():
                    try:
                        cursor.execute(statement)
                    except Exception as exc:
                        if not _is_already_exists_error(exc):
                            raise
                connection.commit()
            self._last_error = None
        except Exception as exc:
            self._last_error = str(exc)
            raise

    def create_vector_index(self) -> None:
        if not self._is_configured():
            raise RuntimeError("Oracle AI Vector Search is missing required database configuration.")
        try:
            with self._connect() as connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(self.vector_index_sql())
                except Exception as exc:
                    if not _is_already_exists_error(exc):
                        raise
                connection.commit()
            self._last_error = None
        except Exception as exc:
            self._last_error = str(exc)
            raise

    def validate_schema(self) -> dict[str, object]:
        if not self._is_configured():
            return {"configured": False, "valid": False, "missing_config": self._missing_config()}
        sql = (
            "SELECT COUNT(*) FROM user_tab_columns "
            "WHERE table_name = UPPER(:table_name) "
            "AND column_name IN ('CHUNK_ID', 'CHUNK_TEXT', 'EMBEDDING', 'METADATA_JSON')"
        )
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(sql, {"table_name": self.config.table_name})
            row = cursor.fetchone()
        column_count = int(row[0]) if row else 0
        return {
            "configured": True,
            "valid": column_count >= 4,
            "required_column_count": column_count,
            "expected_dimensions": self.config.dimensions,
        }

    def chunk_count(self) -> int:
        if not self._is_configured():
            return 0
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {_safe_identifier(self.config.table_name)}")
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def health(self) -> dict[str, object]:
        missing = self._missing_config()
        schema: dict[str, object] = {"configured": False, "valid": False}
        embedding_metadata: dict[str, object] = {}
        chunk_count = 0
        service_count = 0
        service_domain_count = 0
        if not missing:
            try:
                schema = self.validate_schema()
                if schema.get("valid"):
                    chunk_count = self.chunk_count()
                    service_count = self._distinct_count("service")
                    service_domain_count = self._distinct_count("service_domain")
                    embedding_metadata = self._embedding_metadata()
                self._last_error = None
            except Exception as exc:
                self._last_error = str(exc)
        return {
            "provider": "oracle_ai_vector_search",
            "exists": not missing and bool(schema.get("valid")),
            "read_enabled": not missing and bool(schema.get("valid")),
            "table_name": self.config.table_name,
            "index_name": self.config.index_name,
            "embedding_column": self.config.embedding_column,
            "metadata_column": self.config.metadata_column,
            "expected_dimensions": self.config.dimensions,
            "index_embedding_provider": embedding_metadata.get("embedding_provider"),
            "index_embedding_model": embedding_metadata.get("embedding_model"),
            "index_dimensions": embedding_metadata.get("dimensions") or self.config.dimensions,
            "distance_metric": self.config.distance_metric,
            "chunk_count": chunk_count,
            "service_count": service_count,
            "service_domain_count": service_domain_count,
            "missing_config": missing,
            "wallet_location_configured": bool(self.config.wallet_location),
            "wallet_password_configured": bool(self.config.wallet_password),
            "schema": schema,
            "last_error": self._last_error,
            "last_query": self._last_query,
        }

    def schema_sql(self) -> list[str]:
        table = _safe_identifier(self.config.table_name)
        embedding_column = _safe_identifier(self.config.embedding_column)
        metadata_column = _safe_identifier(self.config.metadata_column)
        return [
            f"""
CREATE TABLE {table} (
  chunk_id VARCHAR2(512) PRIMARY KEY,
  source_id VARCHAR2(512),
  title VARCHAR2(1024),
  url VARCHAR2(2048),
  source_type VARCHAR2(128),
  chunk_text CLOB,
  {embedding_column} VECTOR({int(self.config.dimensions)}, FLOAT32),
  {metadata_column} JSON,
  service VARCHAR2(256),
  service_domain VARCHAR2(128),
  service_category VARCHAR2(128),
  category VARCHAR2(128),
  topic VARCHAR2(128),
  intent_tags VARCHAR2(2048),
  architecture_patterns VARCHAR2(2048),
  workload_types VARCHAR2(2048),
  domain_tags VARCHAR2(2048),
  source_url VARCHAR2(2048),
  content_hash VARCHAR2(128),
  updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
)""".strip(),
            f"CREATE INDEX {table}_SERVICE_IDX ON {table} (service)",
            f"CREATE INDEX {table}_DOMAIN_IDX ON {table} (service_domain)",
            f"CREATE INDEX {table}_CATEGORY_IDX ON {table} (category)",
            f"CREATE INDEX {table}_TOPIC_IDX ON {table} (topic)",
            f"CREATE INDEX {table}_HASH_IDX ON {table} (content_hash)",
        ]

    def vector_index_sql(self) -> str:
        table = _safe_identifier(self.config.table_name)
        index = _safe_identifier(self.config.index_name)
        embedding_column = _safe_identifier(self.config.embedding_column)
        metric = _safe_distance_metric(self.config.distance_metric)
        return f"CREATE VECTOR INDEX {index} ON {table} ({embedding_column}) ORGANIZATION NEIGHBOR PARTITIONS DISTANCE {metric}"

    def upsert_sql(self) -> str:
        table = _safe_identifier(self.config.table_name)
        embedding_column = _safe_identifier(self.config.embedding_column)
        metadata_column = _safe_identifier(self.config.metadata_column)
        return f"""
MERGE INTO {table} target
USING (SELECT :chunk_id AS chunk_id FROM dual) source
ON (target.chunk_id = source.chunk_id)
WHEN MATCHED THEN UPDATE SET
  source_id = :source_id,
  title = :title,
  url = :url,
  source_type = :source_type,
  chunk_text = :chunk_text,
  {embedding_column} = TO_VECTOR(:embedding_json),
  {metadata_column} = :metadata_json,
  service = :service,
  service_domain = :service_domain,
  service_category = :service_category,
  category = :category,
  topic = :topic,
  intent_tags = :intent_tags,
  architecture_patterns = :architecture_patterns,
  workload_types = :workload_types,
  domain_tags = :domain_tags,
  source_url = :source_url,
  content_hash = :content_hash,
  updated_at = SYSTIMESTAMP
WHEN NOT MATCHED THEN INSERT (
  chunk_id, source_id, title, url, source_type, chunk_text, {embedding_column}, {metadata_column},
  service, service_domain, service_category, category, topic, intent_tags, architecture_patterns,
  workload_types, domain_tags, source_url, content_hash, updated_at
) VALUES (
  :chunk_id, :source_id, :title, :url, :source_type, :chunk_text, TO_VECTOR(:embedding_json), :metadata_json,
  :service, :service_domain, :service_category, :category, :topic, :intent_tags, :architecture_patterns,
  :workload_types, :domain_tags, :source_url, :content_hash, SYSTIMESTAMP
)""".strip()

    def _search_sql(self, *, top_k: int, filters: VectorSearchFilters) -> tuple[str, dict[str, object]]:
        table = _safe_identifier(self.config.table_name)
        embedding_column = _safe_identifier(self.config.embedding_column)
        metadata_column = _safe_identifier(self.config.metadata_column)
        metric = _safe_distance_metric(self.config.distance_metric)
        where_sql, binds = self._where_clause(filters)
        limit = max(int(top_k), 1)
        sql = f"""
SELECT
  chunk_id,
  title,
  url,
  source_type,
  chunk_text,
  VECTOR_SERIALIZE({embedding_column} RETURNING CLOB) AS embedding_json,
  {metadata_column},
  source_id,
  service,
  service_domain,
  service_category,
  category,
  topic,
  intent_tags,
  architecture_patterns,
  workload_types,
  domain_tags,
  source_url,
  content_hash,
  VECTOR_DISTANCE({embedding_column}, TO_VECTOR(:query_embedding), {metric}) AS vector_distance
FROM {table}
{where_sql}
ORDER BY vector_distance
FETCH FIRST {limit} ROWS ONLY""".strip()
        return sql, binds

    def _where_clause(self, filters: VectorSearchFilters) -> tuple[str, dict[str, object]]:
        metadata_column = _safe_identifier(self.config.metadata_column)
        required: list[str] = []
        soft: list[str] = []
        binds: dict[str, object] = {}
        if filters.service_domain:
            required.append("LOWER(service_domain) = :service_domain")
            binds["service_domain"] = filters.service_domain.lower()
        if filters.trust_level:
            required.append(f"JSON_VALUE({metadata_column}, '$.trust_level') = :trust_level")
            binds["trust_level"] = filters.trust_level
        if filters.min_freshness_score is not None:
            required.append(f"TO_NUMBER(JSON_VALUE({metadata_column}, '$.freshness_score')) >= :min_freshness_score")
            binds["min_freshness_score"] = filters.min_freshness_score

        def add_in(column: str, values: tuple[str, ...], prefix: str) -> None:
            if not values:
                return
            keys = []
            for index, value in enumerate(values):
                key = f"{prefix}_{index}"
                binds[key] = value.lower()
                keys.append(f":{key}")
            soft.append(f"LOWER({column}) IN ({', '.join(keys)})")

        def add_pipe_like(column: str, values: tuple[str, ...], prefix: str) -> None:
            for index, value in enumerate(values):
                key = f"{prefix}_{index}"
                binds[key] = f"%|{_normalize_tag(value)}|%"
                soft.append(f"{column} LIKE :{key}")

        add_in("service", filters.services, "service")
        add_in("service_domain", filters.service_domains, "service_domain_any")
        add_in("topic", filters.topics, "topic")
        add_pipe_like("architecture_patterns", filters.architecture_patterns, "pattern")
        add_pipe_like("workload_types", filters.workload_types, "workload")
        add_pipe_like("domain_tags", filters.domain_tags, "domain")
        if filters.intent:
            add_pipe_like("intent_tags", (filters.intent,), "intent")
        if filters.release_aware:
            add_pipe_like("intent_tags", ("release", "release_awareness"), "release")

        clauses = [*required]
        if soft:
            clauses.append("(" + " OR ".join(soft) + ")")
        return ("WHERE " + " AND ".join(clauses), binds) if clauses else ("", binds)

    def _row_to_result(self, row: Any) -> tuple[VectorChunk, float]:
        (
            chunk_id,
            title,
            url,
            source_type,
            chunk_text,
            embedding_json,
            metadata_json,
            source_id,
            service,
            service_domain,
            service_category,
            category,
            topic,
            intent_tags,
            architecture_patterns,
            workload_types,
            domain_tags,
            source_url,
            content_hash,
            distance,
        ) = row
        metadata = _loads_json(metadata_json)
        metadata.update(
            {
                "source_id": metadata.get("source_id") or source_id,
                "service": metadata.get("service") or service,
                "service_domain": metadata.get("service_domain") or service_domain,
                "service_category": metadata.get("service_category") or service_category,
                "category": metadata.get("category") or category,
                "topic": metadata.get("topic") or topic,
                "intent_tags": metadata.get("intent_tags") or _split_pipe_tags(intent_tags),
                "architecture_patterns": metadata.get("architecture_patterns") or _split_pipe_tags(architecture_patterns),
                "workload_types": metadata.get("workload_types") or _split_pipe_tags(workload_types),
                "domain_tags": metadata.get("domain_tags") or _split_pipe_tags(domain_tags),
                "source_url": metadata.get("source_url") or source_url,
                "content_hash": metadata.get("content_hash") or content_hash,
            }
        )
        embedding = _loads_vector(embedding_json)
        score = 1.0 / (1.0 + max(float(distance or 0.0), 0.0))
        return (
            VectorChunk(
                id=str(chunk_id),
                title=str(title),
                url=str(url) if url else None,
                source_type=str(source_type or "oci_doc"),
                text=str(chunk_text or ""),
                embedding=embedding,
                metadata=metadata,
            ),
            score,
        )

    def _chunk_binds(self, chunk: VectorChunk) -> dict[str, object]:
        metadata = chunk.metadata
        self._validate_embedding(chunk.embedding)
        return {
            "chunk_id": chunk.id,
            "source_id": str(metadata.get("source_id") or ""),
            "title": chunk.title,
            "url": chunk.url,
            "source_type": chunk.source_type,
            "chunk_text": chunk.text,
            "embedding_json": json.dumps(chunk.embedding),
            "metadata_json": json.dumps(metadata),
            "service": metadata.get("service"),
            "service_domain": metadata.get("service_domain"),
            "service_category": metadata.get("service_category"),
            "category": metadata.get("category"),
            "topic": metadata.get("topic"),
            "intent_tags": _pipe_tags(metadata.get("intent_tags", [])),
            "architecture_patterns": _pipe_tags(metadata.get("architecture_patterns", [])),
            "workload_types": _pipe_tags(metadata.get("workload_types", [])),
            "domain_tags": _pipe_tags(metadata.get("domain_tags", [])),
            "source_url": metadata.get("source_url") or chunk.url,
            "content_hash": metadata.get("content_hash"),
        }

    def _set_upsert_input_sizes(self, cursor: Any) -> None:
        set_input_sizes = getattr(cursor, "setinputsizes", None)
        if set_input_sizes is None:
            return
        try:
            import oracledb
        except ImportError:
            return
        clob_type = getattr(oracledb, "DB_TYPE_CLOB", None) or getattr(oracledb, "CLOB", None)
        if clob_type is None:
            return
        set_input_sizes(
            chunk_text=clob_type,
            embedding_json=clob_type,
            metadata_json=clob_type,
        )

    def _set_search_input_sizes(self, cursor: Any) -> None:
        set_input_sizes = getattr(cursor, "setinputsizes", None)
        if set_input_sizes is None:
            return
        try:
            import oracledb
        except ImportError:
            return
        clob_type = getattr(oracledb, "DB_TYPE_CLOB", None) or getattr(oracledb, "CLOB", None)
        if clob_type is None:
            return
        set_input_sizes(query_embedding=clob_type)

    def _connect(self) -> Any:
        if self.connection_factory:
            return self.connection_factory()
        try:
            import oracledb
        except ImportError as exc:
            raise RuntimeError("python-oracledb is required for Oracle AI Vector Search retrieval.") from exc
        connect_args: dict[str, object] = {
            "user": self.config.username,
            "password": self.config.password,
            "dsn": self.config.dsn,
            "tcp_connect_timeout": self.config.connect_timeout_seconds,
        }
        if self.config.wallet_location:
            connect_args["config_dir"] = self.config.wallet_location
            connect_args["wallet_location"] = self.config.wallet_location
        if self.config.wallet_password:
            connect_args["wallet_password"] = self.config.wallet_password
        create_pool = getattr(oracledb, "create_pool", None)
        if create_pool is None:
            return oracledb.connect(**connect_args)
        with self._pool_lock:
            if self._pool is None:
                self._pool = create_pool(
                    min=1,
                    max=4,
                    increment=1,
                    **connect_args,
                )
        return self._pool.acquire()

    def _is_configured(self) -> bool:
        return not self._missing_config()

    def _missing_config(self) -> list[str]:
        return [
            name
            for name, value in (
                ("OCI_VECTOR_DB_DSN", self.config.dsn),
                ("OCI_VECTOR_DB_USER", self.config.username),
                ("OCI_VECTOR_DB_PASSWORD", self.config.password),
            )
            if not value
        ]

    def _validate_embedding(self, embedding: list[float]) -> None:
        if not embedding:
            raise ValueError("Vector embedding is empty.")
        if len(embedding) != self.config.dimensions:
            raise ValueError(
                f"Vector embedding dimension mismatch: expected {self.config.dimensions}, got {len(embedding)}."
            )

    def _embedding_metadata(self) -> dict[str, object]:
        table = _safe_identifier(self.config.table_name)
        metadata_column = _safe_identifier(self.config.metadata_column)
        sql = f"""
SELECT {metadata_column}
FROM {table}
WHERE {metadata_column} IS NOT NULL
FETCH FIRST 1 ROWS ONLY""".strip()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(sql)
            row = cursor.fetchone()
        metadata = _loads_json(row[0]) if row else {}
        dimensions = metadata.get("embedding_dimensions") or metadata.get("dimensions")
        return {
            "embedding_provider": metadata.get("embedding_provider"),
            "embedding_model": metadata.get("embedding_model"),
            "dimensions": int(dimensions) if dimensions is not None else None,
        }

    def _filter_summary(self, filters: VectorSearchFilters) -> dict[str, object]:
        return {
            "intent": filters.intent,
            "service_domain": filters.service_domain,
            "service_domains": list(filters.service_domains),
            "services": list(filters.services),
            "architecture_patterns": list(filters.architecture_patterns),
            "workload_types": list(filters.workload_types),
            "domain_tags": list(filters.domain_tags),
            "topics": list(filters.topics),
            "release_aware": filters.release_aware,
        }

    def _distinct_count(self, column: str) -> int:
        table = _safe_identifier(self.config.table_name)
        safe_column = _safe_identifier(column)
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT COUNT(DISTINCT {safe_column}) FROM {table} WHERE {safe_column} IS NOT NULL")
            row = cursor.fetchone()
        return int(row[0]) if row else 0


class FallbackVectorStore:
    def __init__(self, primary: VectorStore, fallback: VectorStore, provider_name: str) -> None:
        self.primary = primary
        self.fallback = fallback
        self.provider_name = provider_name
        self._last_fallback_reason: str | None = None

    @property
    def exists(self) -> bool:
        return self.primary.exists or self.fallback.exists

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 4,
        filters: VectorSearchFilters | None = None,
    ) -> list[tuple[VectorChunk, float]]:
        if self.primary.exists:
            try:
                results = self.primary.search(query_embedding=query_embedding, top_k=top_k, filters=filters)
                self._last_fallback_reason = None
                return results
            except Exception as exc:
                self._last_fallback_reason = str(exc)
        else:
            self._last_fallback_reason = "primary provider unavailable"
        return self.fallback.search(query_embedding=query_embedding, top_k=top_k, filters=filters)

    def health(self) -> dict[str, object]:
        primary_health = self.primary.health()
        fallback_health = self.fallback.health()
        fallback_active = not bool(primary_health.get("exists"))
        active_health = fallback_health if fallback_active else primary_health
        return {
            "provider": self.provider_name,
            "exists": bool(primary_health.get("exists")) or bool(fallback_health.get("exists")),
            "fallback_enabled": True,
            "fallback_active": fallback_active,
            "fallback_reason": self._last_fallback_reason,
            "active_store": "fallback" if fallback_active else "primary",
            "index_embedding_provider": active_health.get("index_embedding_provider"),
            "index_embedding_model": active_health.get("index_embedding_model"),
            "index_dimensions": active_health.get("index_dimensions"),
            "primary": primary_health,
            "fallback": fallback_health,
            "chunk_count": (
                int(primary_health.get("chunk_count", 0))
                if not fallback_active
                else int(fallback_health.get("chunk_count", 0))
            ),
            "service_count": (
                int(primary_health.get("service_count", 0))
                if not fallback_active
                else int(fallback_health.get("service_count", 0))
            ),
            "service_domain_count": (
                int(primary_health.get("service_domain_count", 0))
                if not fallback_active
                else int(fallback_health.get("service_domain_count", 0))
            ),
        }


def _metadata_soft_match(metadata: dict[str, Any], filters: VectorSearchFilters) -> bool:
    if not filters.has_metadata_filters():
        return True
    service = str(metadata.get("service", "")).lower()
    domain = str(metadata.get("service_domain", "")).lower()
    patterns = {str(pattern).lower() for pattern in metadata.get("architecture_patterns", [])}
    workloads = {str(workload).lower() for workload in metadata.get("workload_types", [])}
    domains = {str(tag).lower() for tag in metadata.get("domain_tags", [])}
    topic = str(metadata.get("topic", "")).lower()
    intents = {str(tag).lower() for tag in metadata.get("intent_tags", [])}
    if filters.intent and filters.intent.lower() in intents:
        return True
    if service and service in {item.lower() for item in filters.services}:
        return True
    if domain and domain in {item.lower() for item in filters.service_domains}:
        return True
    if topic and topic in {item.lower() for item in filters.topics}:
        return True
    if patterns.intersection({item.lower() for item in filters.architecture_patterns}):
        return True
    if workloads.intersection({item.lower() for item in filters.workload_types}):
        return True
    if domains.intersection({item.lower() for item in filters.domain_tags}):
        return True
    if filters.release_aware and "release" in intents:
        return True
    return not (
        filters.intent
        or filters.service_domains
        or filters.services
        or filters.architecture_patterns
        or filters.workload_types
        or filters.domain_tags
        or filters.topics
        or filters.release_aware
    )


def _safe_identifier(value: str) -> str:
    cleaned = value.upper()
    if not cleaned.replace("_", "").isalnum():
        raise ValueError(f"Unsafe Oracle identifier: {value}")
    return cleaned


def _safe_distance_metric(value: str) -> str:
    metric = value.upper()
    if metric not in {"COSINE", "EUCLIDEAN", "DOT"}:
        raise ValueError(f"Unsupported Oracle vector distance metric: {value}")
    return metric


def _normalize_tag(value: object) -> str:
    return str(value).strip().lower().replace("|", " ")


def _pipe_tags(values: object) -> str:
    if isinstance(values, str):
        items = [values]
    else:
        try:
            items = list(values)  # type: ignore[arg-type]
        except TypeError:
            items = []
    normalized = [_normalize_tag(item) for item in items if str(item)]
    return "|" + "|".join(dict.fromkeys(normalized)) + "|" if normalized else ""


def _split_pipe_tags(value: object) -> list[str]:
    if not value:
        return []
    return [item for item in str(value).split("|") if item]


def _loads_json(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "read"):
        value = value.read()
    if not value:
        return {}
    return json.loads(str(value))


def _loads_vector(value: object) -> list[float]:
    if isinstance(value, list):
        return [float(item) for item in value]
    if hasattr(value, "read"):
        value = value.read()
    if not value:
        return []
    return [float(item) for item in json.loads(str(value))]


def _is_already_exists_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "ora-00955" in message or "already used by an existing object" in message
