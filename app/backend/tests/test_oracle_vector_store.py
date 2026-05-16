import json
import sys
import types
from decimal import Decimal

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.services.embeddings import LocalHashingEmbedder
from oci_arch_studio_backend.services.intents import Intent, get_intent_profile
from oci_arch_studio_backend.services.retrieval import build_retriever
from oci_arch_studio_backend.services.vector_store import (
    OracleAiVectorSearchConfig,
    OracleAiVectorSearchStore,
    VectorChunk,
    VectorSearchFilters,
)


def test_oracle_vector_store_generates_schema_and_vector_index_sql() -> None:
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            table_name="OCI_ARCHITECTURE_CHUNKS",
            index_name="OCI_ARCH_CHUNKS_VEC_IDX",
            dimensions=256,
        )
    )

    schema = "\n".join(store.schema_sql())
    index_sql = store.vector_index_sql()

    assert "EMBEDDING VECTOR(256, FLOAT32)" in schema
    assert "METADATA_JSON JSON" in schema
    assert "CREATE VECTOR INDEX OCI_ARCH_CHUNKS_VEC_IDX" in index_sql
    assert "DISTANCE COSINE" in index_sql


def test_oracle_vector_search_builds_metadata_filters_and_returns_chunks() -> None:
    connection = FakeConnection(
        search_rows=[
            (
                "logging::1",
                "OCI Logging",
                "https://example.com/logging",
                "oci_doc",
                "OCI Logging centralizes logs.",
                "[0.1, 0.2]",
                json.dumps(
                    {
                        "service": "Logging",
                        "service_domain": "observability",
                        "intent_tags": ["observability"],
                        "source_url": "https://example.com/logging",
                    }
                ),
                "oci-logging",
                "Logging",
                "observability",
                "observability",
                "observability",
                "observability",
                "|observability|",
                "|operational-visibility|",
                "|enterprise-app|",
                "|enterprise|",
                "https://example.com/logging",
                "hash",
                0.25,
            )
        ]
    )
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn="db",
            username="user",
            password="pw",
            dimensions=2,
        ),
        connection_factory=lambda: connection,
    )

    results = store.search(
        [0.1, 0.2],
        top_k=3,
        filters=VectorSearchFilters(
            intent="observability",
            service_domains=("observability", "security"),
            services=("Logging",),
            architecture_patterns=("operational-visibility",),
            workload_types=("enterprise-app",),
            domain_tags=("enterprise",),
            topics=("observability",),
        ),
    )

    chunk, score = results[0]
    assert chunk.id == "logging::1"
    assert chunk.metadata["service"] == "Logging"
    assert chunk.metadata["service_domain"] == "observability"
    assert round(score, 3) == 0.8
    assert "VECTOR_DISTANCE" in connection.last_execute_sql
    assert "LOWER(service) IN (:service_0)" in connection.last_execute_sql
    assert connection.last_execute_binds["service_0"] == "logging"
    assert connection.last_execute_binds["intent_0"] == "%|observability|%"


def test_oracle_vector_search_binds_large_query_vector_as_clob(monkeypatch) -> None:
    clob_type = object()
    monkeypatch.setitem(sys.modules, "oracledb", types.SimpleNamespace(DB_TYPE_CLOB=clob_type))
    connection = FakeConnection(
        search_rows=[
            (
                "genai::1",
                "OCI Generative AI",
                "https://example.com/genai",
                "oci_doc",
                "Generative AI supports semantic embeddings.",
                json.dumps([0.1] * 1536),
                json.dumps({"service": "Generative AI", "service_domain": "ai_ml"}),
                "oci-genai",
                "Generative AI",
                "ai_ml",
                "ai_ml",
                "embeddings",
                "embeddings",
                "|ai_inference|",
                "|rag|",
                "|enterprise-app|",
                "|enterprise|",
                "https://example.com/genai",
                "hash",
                0.1,
            )
        ]
    )
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn="db",
            username="user",
            password="pw",
            dimensions=1536,
        ),
        connection_factory=lambda: connection,
    )

    results = store.search([0.1] * 1536)

    assert results[0][0].id == "genai::1"
    assert connection.last_input_sizes["query_embedding"] is clob_type
    assert len(connection.last_execute_binds["query_embedding"]) > 4000


def test_oracle_vector_upsert_serializes_metadata_and_tags() -> None:
    connection = FakeConnection()
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn="db",
            username="user",
            password="pw",
            dimensions=2,
        ),
        connection_factory=lambda: connection,
    )
    chunk = VectorChunk(
        id="object::1",
        title="OCI Object Storage",
        url="https://example.com/object",
        source_type="oci_doc",
        text="Object Storage stores artifacts.",
        embedding=[0.4, 0.6],
        metadata={
            "source_id": "oci-object",
            "service": "Object Storage",
            "service_domain": "storage",
            "service_category": "storage",
            "category": "cost-optimization",
            "topic": "architecture",
            "intent_tags": ["architecture", "cost"],
            "architecture_patterns": ["lifecycle-management"],
            "workload_types": ["webapp"],
            "domain_tags": ["ecommerce"],
            "source_url": "https://example.com/object",
            "content_hash": "abc",
        },
    )

    assert store.upsert_chunks([chunk]) == 1

    row = connection.last_executemany_rows[0]
    assert row["embedding_json"] == "[0.4, 0.6]"
    assert row["intent_tags"] == "|architecture|cost|"
    assert row["architecture_patterns"] == "|lifecycle-management|"
    assert json.loads(row["metadata_json"])["service"] == "Object Storage"
    assert connection.committed is True


def test_oracle_vector_upsert_binds_large_json_as_clob(monkeypatch) -> None:
    clob_type = object()
    monkeypatch.setitem(sys.modules, "oracledb", types.SimpleNamespace(DB_TYPE_CLOB=clob_type))
    connection = FakeConnection()
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn="db",
            username="user",
            password="pw",
            dimensions=1536,
        ),
        connection_factory=lambda: connection,
    )
    chunk = VectorChunk(
        id="genai::1",
        title="OCI Generative AI",
        url="https://example.com/genai",
        source_type="oci_doc",
        text="Generative AI supports semantic embeddings.",
        embedding=[0.123456789] * 1536,
        metadata={
            "source_id": "oci-genai",
            "service": "Generative AI",
            "service_domain": "ai_ml",
            "embedding_provider": "oci_genai",
            "embedding_model": "cohere.embed-v4.0",
            "embedding_dimensions": 1536,
        },
    )

    assert store.upsert_chunks([chunk]) == 1

    assert connection.last_input_sizes["chunk_text"] is clob_type
    assert connection.last_input_sizes["embedding_json"] is clob_type
    assert connection.last_input_sizes["metadata_json"] is clob_type
    assert len(connection.last_executemany_rows[0]["embedding_json"]) > 4000


def test_oracle_vector_health_reports_embedding_metadata() -> None:
    connection = FakeConnection(
        metadata_row={
            "embedding_provider": "oci_genai",
            "embedding_model": "cohere.embed-v4.0",
            "embedding_dimensions": Decimal("1536"),
        }
    )
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn="db",
            username="user",
            dimensions=1536,
            **{"password": "placeholder"},
        ),
        connection_factory=lambda: connection,
    )

    health = store.health()

    assert health["index_embedding_provider"] == "oci_genai"
    assert health["index_embedding_model"] == "cohere.embed-v4.0"
    assert health["index_dimensions"] == 1536


def test_oracle_vector_retriever_uses_local_fallback_when_unconfigured(tmp_path) -> None:
    embedder = LocalHashingEmbedder()
    index_path = tmp_path / "index.json"
    text = "OCI Monitoring provides metrics and alarms."
    index_path.write_text(
        json.dumps(
            {
                "chunks": [
                    {
                        "id": "monitoring::1",
                        "title": "OCI Monitoring",
                        "url": "https://example.com/monitoring",
                        "source_type": "oci_doc",
                        "text": text,
                        "embedding": embedder.embed(text),
                        "metadata": {
                            "service": "Monitoring",
                            "service_domain": "observability",
                            "intent_tags": ["observability"],
                            "architecture_patterns": ["operational-visibility"],
                            "freshness_score": 0.9,
                            "trust_level": "official",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    retriever = build_retriever(
        Settings(
            KNOWLEDGE_INDEX_PATH=index_path,
            RETRIEVAL_PROVIDER="oracle_ai_vector_search",
        )
    )

    import asyncio

    results = asyncio.run(retriever.retrieve("Show observability metrics.", get_intent_profile(Intent.OBSERVABILITY)))
    diagnostics = retriever.diagnostics()

    assert results[0].chunk_id == "monitoring::1"
    assert diagnostics["provider"] == "oracle_ai_vector_search"
    assert diagnostics["store"]["fallback_enabled"] is True
    assert diagnostics["store"]["fallback_active"] is True


def test_oracle_vector_store_passes_wallet_connection_arguments(monkeypatch) -> None:
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return FakeConnection()

    monkeypatch.setitem(sys.modules, "oracledb", types.SimpleNamespace(connect=fake_connect))
    store = OracleAiVectorSearchStore(
        OracleAiVectorSearchConfig(
            dsn="ociarchvec_high",
            username="ADMIN",
            password="pw",
            wallet_location="/opt/oci-architecture-studio/secrets/wallet",
            wallet_password="wallet-pw",
        )
    )

    connection = store._connect()

    assert isinstance(connection, FakeConnection)
    assert captured["dsn"] == "ociarchvec_high"
    assert captured["config_dir"] == "/opt/oci-architecture-studio/secrets/wallet"
    assert captured["wallet_location"] == "/opt/oci-architecture-studio/secrets/wallet"
    assert captured["wallet_password"] == "wallet-pw"


class FakeConnection:
    def __init__(self, search_rows=None, metadata_row=None) -> None:
        self.search_rows = search_rows or []
        self.metadata_row = metadata_row
        self.last_execute_sql = ""
        self.last_execute_binds = {}
        self.last_executemany_sql = ""
        self.last_executemany_rows = []
        self.last_input_sizes = {}
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return FakeCursor(self)

    def commit(self) -> None:
        self.committed = True


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def execute(self, sql, binds=None) -> None:
        self.connection.last_execute_sql = sql
        self.connection.last_execute_binds = binds or {}

    def executemany(self, sql, rows) -> None:
        self.connection.last_executemany_sql = sql
        self.connection.last_executemany_rows = rows

    def fetchone(self):
        if "user_tab_columns" in self.connection.last_execute_sql:
            return (4,)
        if "FETCH FIRST 1 ROWS ONLY" in self.connection.last_execute_sql:
            return (self.connection.metadata_row,) if self.connection.metadata_row else None
        if "COUNT(*)" in self.connection.last_execute_sql:
            return (len(self.connection.search_rows),)
        return None

    def fetchall(self):
        return self.connection.search_rows

    def setinputsizes(self, **kwargs) -> None:
        self.connection.last_input_sizes = kwargs
