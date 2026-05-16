from pathlib import Path
from time import perf_counter

from oci_arch_studio_backend.core.config import Settings
from oci_arch_studio_backend.models.architecture import RetrievedSource, RetrievalDebugTrace, RetrievalScoreTrace
from oci_arch_studio_backend.services.architecture_heuristics import (
    ArchitectureDomainHeuristics,
    ArchitectureHeuristicClassifier,
)
from oci_arch_studio_backend.services.architecture_patterns import ArchitecturePatternSelector
from oci_arch_studio_backend.services.architecture_reasoning_engine import ArchitectureReasoningEngine, ReasoningProfile
from oci_arch_studio_backend.services.embeddings import (
    Embedder,
    FallbackEmbedder,
    LocalHashingEmbedder,
    OciGenerativeAiEmbedder,
    OciGenerativeAiEmbeddingConfig,
)
from oci_arch_studio_backend.services.freshness import is_stale_source
from oci_arch_studio_backend.services.intents import IntentProfile
from oci_arch_studio_backend.services.retrieval_metrics import retrieval_metrics
from oci_arch_studio_backend.services.retrieval_reranker import RetrievalReranker
from oci_arch_studio_backend.services.service_mapping import OciServiceMapper
from oci_arch_studio_backend.services.vector_store import (
    FallbackVectorStore,
    JsonVectorStore,
    OracleAiVectorSearchConfig,
    OracleAiVectorSearchStore,
    OciObjectStorageVectorConfig,
    OciObjectStorageVectorStore,
    UnavailableVectorStore,
    VectorSearchFilters,
    VectorStore,
)


INTENT_RETRIEVAL_HINTS: dict[str, dict[str, tuple[str, ...]]] = {
    "architecture": {
        "service_domains": ("architecture", "networking", "compute", "database", "storage", "edge"),
        "architecture_patterns": ("reference-architecture", "high-availability", "public-ingress", "data-tier"),
        "workload_types": ("webapp", "ecommerce", "enterprise-app"),
        "domain_tags": ("ecommerce", "SaaS", "enterprise"),
        "topics": ("architecture",),
    },
    "migration": {
        "service_domains": ("containers", "database"),
        "architecture_patterns": ("migration-waves", "cutover", "container-platform"),
        "workload_types": ("migration", "saas-platform", "enterprise-app"),
        "domain_tags": ("enterprise", "SaaS"),
        "topics": ("migration",),
    },
    "dr": {
        "service_domains": ("resilience", "database", "security", "networking", "storage", "observability"),
        "architecture_patterns": ("disaster-recovery", "failover-runbook", "backup-recovery", "operational-visibility", "auditability"),
        "workload_types": ("regulated-workload", "enterprise-app"),
        "domain_tags": ("fintech", "enterprise"),
        "topics": ("disaster-recovery",),
    },
    "cost": {
        "service_domains": ("cost", "compute", "storage", "database"),
        "architecture_patterns": ("budgets", "rightsizing", "lifecycle-management", "autoscaling"),
        "workload_types": ("cost-optimized-webapp", "webapp", "enterprise-app"),
        "domain_tags": ("ecommerce", "SaaS", "enterprise"),
        "topics": ("cost-optimization",),
    },
    "security": {
        "service_domains": ("security", "networking"),
        "architecture_patterns": ("least-privilege", "auditability", "network-isolation"),
        "workload_types": ("regulated-workload", "enterprise-app"),
        "domain_tags": ("fintech", "enterprise"),
        "topics": ("architecture",),
    },
    "release_awareness": {
        "service_domains": ("architecture", "resilience", "database", "networking", "compute", "storage", "observability"),
        "architecture_patterns": ("well-architected", "operational-excellence", "high-availability"),
        "workload_types": ("enterprise-app", "migration", "webapp"),
        "domain_tags": ("enterprise",),
        "topics": ("architecture", "migration", "cost-optimization"),
    },
    "observability": {
        "service_domains": ("observability", "security", "database", "compute", "containers"),
        "architecture_patterns": ("operational-visibility", "auditability", "alarms", "slo-monitoring"),
        "workload_types": ("enterprise-app", "regulated-workload", "saas-platform"),
        "domain_tags": ("enterprise", "fintech", "SaaS"),
        "topics": ("observability",),
    },
    "ai_ml": {
        "service_domains": ("compute", "containers", "storage", "networking", "observability", "security", "cost"),
        "architecture_patterns": ("application-tier", "autoscaling", "operational-visibility", "key-management"),
        "workload_types": ("ai-inference", "enterprise-app"),
        "domain_tags": ("AI/ML", "enterprise"),
        "topics": ("architecture", "observability", "cost-optimization"),
    },
    "modernization": {
        "service_domains": ("containers", "database", "networking", "security", "observability"),
        "architecture_patterns": ("container-platform", "managed-database", "migration-waves", "cutover"),
        "workload_types": ("migration", "enterprise-app", "webapp"),
        "domain_tags": ("enterprise", "SaaS"),
        "topics": ("migration",),
    },
    "saas_platform": {
        "service_domains": ("networking", "containers", "compute", "database", "storage", "edge", "security", "observability", "cost"),
        "architecture_patterns": ("high-availability", "network-isolation", "tagging", "operational-visibility"),
        "workload_types": ("saas-platform", "webapp", "enterprise-app"),
        "domain_tags": ("SaaS", "enterprise"),
        "topics": ("architecture", "disaster-recovery", "cost-optimization", "observability"),
    },
    "analytics": {
        "service_domains": ("database", "storage", "observability", "security", "cost"),
        "architecture_patterns": ("managed-database", "data-tier", "lifecycle-management", "operational-visibility"),
        "workload_types": ("analytics", "enterprise-app"),
        "domain_tags": ("enterprise",),
        "topics": ("architecture", "cost-optimization", "observability"),
    },
}

SERVICE_QUERY_TERMS: dict[str, tuple[str, ...]] = {
    "Audit": ("audit", "audit trails", "audit evidence"),
    "Cloud Guard": ("cloud guard", "posture management", "threat detection"),
    "Container Registry": ("container registry", "image registry", "ecr"),
    "Database Migration": ("database migration", "rds", "database migration service"),
    "DNS": ("dns", "traffic steering", "traffic failover"),
    "Full Stack Disaster Recovery": ("full stack disaster recovery", "disaster recovery", "dr runbook"),
    "Load Balancer": ("load balancer", "load balancing"),
    "Logging": ("logging", "logs", "audit"),
    "Monitoring": ("monitoring", "metrics", "alarms"),
    "Vault": ("vault", "secrets", "keys"),
    "Virtual Cloud Network": ("vcn", "virtual cloud network", "network segmentation"),
    "Web Application Firewall": ("waf", "web application firewall"),
    "Identity and Access Management": ("iam", "identity", "policies"),
    "Autonomous Database": ("autonomous database", "adb"),
    "Network Security Groups": ("network security group", "network security groups", "nsg"),
}


class OciKnowledgeRetriever:
    """Retrieves OCI knowledge chunks from the local JSON vector index."""

    def __init__(
        self,
        index_path: Path,
        top_k: int = 6,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
        provider_name: str = "local_json",
        debug_enabled: bool = False,
        candidate_multiplier: int = 6,
    ) -> None:
        self.store = store or JsonVectorStore(index_path=index_path)
        self.top_k = top_k
        self.embedder = embedder or LocalHashingEmbedder()
        self.provider_name = provider_name
        self.service_mapper = OciServiceMapper()
        self.heuristic_classifier = ArchitectureHeuristicClassifier()
        self.pattern_selector = ArchitecturePatternSelector()
        self.reasoning_engine = ArchitectureReasoningEngine()
        self.reranker = RetrievalReranker()
        self.debug_enabled = debug_enabled
        self.candidate_multiplier = max(candidate_multiplier, 1)
        self.last_debug_trace: RetrievalDebugTrace | None = None

    async def retrieve(
        self,
        question: str,
        intent_profile: IntentProfile | None = None,
        *,
        workload_context: str | None = None,
        debug_enabled: bool | None = None,
    ) -> list[RetrievedSource]:
        started_at = retrieval_metrics.start()
        self.last_debug_trace = None
        intent = intent_profile.intent.value if intent_profile else None
        if not self.store.exists:
            sources = self._missing_index_sources()
            retrieval_metrics.record(
                started_at=started_at,
                provider=self.provider_name,
                embedding_model=self.embedder.model_name,
                result_count=len(sources),
                intent=intent,
                missing_index=True,
                warning="retrieval index is missing or unreachable",
            )
            return sources

        combined_text = " ".join(part for part in (question, workload_context) if part)
        service_mapping = self.service_mapper.map_text(combined_text)
        heuristics = self.heuristic_classifier.detect(combined_text)
        explicit_services = self._explicit_query_services(question)
        reasoning_profile = (
            self.reasoning_engine.select_profile(
                question=question,
                workload_context=workload_context,
                profile=intent_profile,
                sources=[],
            )
            if intent_profile
            else None
        )
        pattern = self.pattern_selector.select(
            question=question,
            workload_context=workload_context,
            profile=intent_profile,
            sources=[],
        ) if intent_profile else None
        pattern_services = (
            self._critical_pattern_services(pattern.name, intent)
            if pattern and self._pattern_triggered(pattern.triggers, combined_text)
            else ()
        )
        retrieval_query = self._build_retrieval_query(question, intent_profile)
        if service_mapping.retrieval_terms:
            retrieval_query = " ".join((retrieval_query, *service_mapping.retrieval_terms))
        if heuristics.retrieval_terms:
            retrieval_query = " ".join((retrieval_query, *heuristics.retrieval_terms))
        if reasoning_profile:
            retrieval_query = " ".join((retrieval_query, *reasoning_profile.retrieval_terms, *reasoning_profile.architecture_patterns))
        embedding_started_at = perf_counter()
        query_embedding = self.embedder.embed(retrieval_query)
        embedding_latency_ms = round((perf_counter() - embedding_started_at) * 1000, 2)
        filters = self._build_filters(
            question,
            intent_profile,
            service_mapping.mapped_services,
            heuristics,
            reasoning_profile,
            explicit_services=explicit_services,
        )
        candidate_count = max(
            self.top_k * self.candidate_multiplier,
            self.top_k + 4,
            self.top_k + (len(service_mapping.mapped_services) * 3),
        )
        results = self.store.search(
            query_embedding=query_embedding,
            top_k=candidate_count,
            filters=filters,
        )

        if not results:
            sources = self._missing_index_sources()
            retrieval_metrics.record(
                started_at=started_at,
                provider=self.provider_name,
                embedding_model=self.embedder.model_name,
                result_count=0,
                intent=intent,
                embedding_latency_ms=embedding_latency_ms,
                missing_index=True,
                no_results=True,
                warning="retrieval returned no matching chunks",
            )
            return sources

        reranked, rerank_traces = self.reranker.rerank(
            results,
            filters=filters,
            service_mapping=service_mapping,
            heuristics=heuristics,
        )
        selected = self._select_final_chunks(
            reranked,
            mapped_services=tuple(dict.fromkeys((*explicit_services, *service_mapping.mapped_services))),
            pattern_services=pattern_services,
            intent=intent,
        )
        sources = [self._to_retrieved_source(chunk, score) for chunk, score in selected]
        if self._debug_requested(debug_enabled):
            self.last_debug_trace = RetrievalDebugTrace(
                provider=self.provider_name,
                detected_intent=intent,
                mapped_oci_services=list(service_mapping.mapped_services),
                mapped_service_summary=service_mapping.summary(),
                domain_heuristics=list(heuristics.domains),
                metadata_filters=self._filter_debug(filters),
                retrieved_chunk_ids=[chunk.id for chunk, _score in results],
                retrieved_chunk_diversity=self._chunk_diversity(results),
                retrieval_scores=[
                    RetrievalScoreTrace(
                        chunk_id=trace.chunk_id,
                        title=trace.title,
                        base_score=trace.base_score,
                        final_score=trace.final_score,
                        adjustments=trace.adjustments,
                    )
                    for trace in rerank_traces
                ],
                selected_final_chunks=[source.chunk_id or source.title for source in sources],
            )
        retrieval_metrics.record(
            started_at=started_at,
            provider=self.provider_name,
            embedding_model=self.embedder.model_name,
            result_count=len(sources),
            intent=intent,
            embedding_latency_ms=embedding_latency_ms,
        )
        return sources

    def diagnostics(self) -> dict[str, object]:
        embedding_diagnostics = (
            self.embedder.diagnostics()
            if hasattr(self.embedder, "diagnostics")
            else {
                "primary_model": self.embedder.model_name,
                "fallback_enabled": False,
            }
        )
        return {
            "provider": self.provider_name,
            "embedding_model": self.embedder.model_name,
            "embedding_provider": self.embedder.model_name,
            "embedding": embedding_diagnostics,
            "store": self.store.health(),
            "metrics": retrieval_metrics.snapshot(),
        }

    def _to_retrieved_source(self, chunk, score: float) -> RetrievedSource:
        metadata = chunk.metadata
        source_url = metadata.get("source_url") or chunk.url
        freshness_value = _metadata_float(metadata.get("freshness_score"))
        fetched_timestamp = metadata.get("fetched_timestamp")
        fetched_value = str(fetched_timestamp) if fetched_timestamp else None
        return RetrievedSource(
            chunk_id=chunk.id,
            title=chunk.title,
            source_type=chunk.source_type,
            url=chunk.url,
            source_url=str(source_url) if source_url else None,
            service=str(metadata.get("service")) if metadata.get("service") else None,
            service_domain=str(metadata.get("service_domain")) if metadata.get("service_domain") else None,
            service_category=str(metadata.get("service_category")) if metadata.get("service_category") else None,
            category=str(metadata.get("category")) if metadata.get("category") else None,
            pattern=str(metadata.get("pattern")) if metadata.get("pattern") else None,
            workload=str(metadata.get("workload")) if metadata.get("workload") else None,
            workload_types=[str(tag) for tag in metadata.get("workload_types", [])],
            domain=str(metadata.get("domain")) if metadata.get("domain") else None,
            domain_tags=[str(tag) for tag in metadata.get("domain_tags", [])],
            topic=str(metadata.get("topic")) if metadata.get("topic") else None,
            migration_mappings={str(key): str(value) for key, value in metadata.get("migration_mappings", {}).items()},
            ha_dr_tags=[str(tag) for tag in metadata.get("ha_dr_tags", [])],
            cost_optimization_tags=[str(tag) for tag in metadata.get("cost_optimization_tags", [])],
            intent_tags=[str(tag) for tag in metadata.get("intent_tags", [])],
            fetched_timestamp=fetched_value,
            freshness_score=freshness_value,
            trust_level=str(metadata.get("trust_level")) if metadata.get("trust_level") else None,
            architecture_patterns=[str(pattern) for pattern in metadata.get("architecture_patterns", [])],
            is_stale=is_stale_source(fetched_value, freshness_value),
            summary=chunk.text,
            relevance_score=round(score, 4),
        )

    def _missing_index_sources(self) -> list[RetrievedSource]:
        return [
            RetrievedSource(
                chunk_id="missing-index",
                title="Local OCI RAG index",
                source_type="missing_index",
                url=None,
                summary=(
                    "No local vector index was found. Run "
                    "`python knowledge/ingestion/ingest.py` from the repository root "
                    "to build `knowledge/snapshots/oci-rag-index.json`."
                ),
                relevance_score=0.0,
            ),
        ]

    def _build_retrieval_query(
        self,
        question: str,
        intent_profile: IntentProfile | None,
    ) -> str:
        if intent_profile is None:
            return question
        return " ".join((question, intent_profile.focus, *intent_profile.retrieval_terms))

    def _build_filters(
        self,
        question: str,
        intent_profile: IntentProfile | None,
        mapped_services: tuple[str, ...] = (),
        heuristics: ArchitectureDomainHeuristics | None = None,
        reasoning_profile: ReasoningProfile | None = None,
        explicit_services: tuple[str, ...] | None = None,
    ) -> VectorSearchFilters:
        if intent_profile is None:
            return VectorSearchFilters()
        explicit_services = explicit_services if explicit_services is not None else self._explicit_query_services(question)
        services = tuple(dict.fromkeys((*explicit_services, *mapped_services)))
        hints = INTENT_RETRIEVAL_HINTS.get(intent_profile.intent.value, {})
        if not hints:
            return VectorSearchFilters()
        heuristics = heuristics or ArchitectureDomainHeuristics()
        reasoning_patterns = reasoning_profile.architecture_patterns if reasoning_profile else ()
        reasoning_workloads = reasoning_profile.workload_types if reasoning_profile else ()
        reasoning_services = reasoning_profile.service_priorities if reasoning_profile else ()
        return VectorSearchFilters(
            intent=intent_profile.intent.value,
            service_domains=tuple(dict.fromkeys((*hints.get("service_domains", ()), *heuristics.service_domains))),
            architecture_patterns=tuple(dict.fromkeys((*hints.get("architecture_patterns", ()), *heuristics.architecture_patterns, *reasoning_patterns))),
            workload_types=tuple(dict.fromkeys((*hints.get("workload_types", ()), *heuristics.workload_types, *reasoning_workloads))),
            domain_tags=tuple(dict.fromkeys((*hints.get("domain_tags", ()), *heuristics.domain_tags))),
            topics=tuple(dict.fromkeys((*hints.get("topics", ()), *heuristics.topics))),
            services=tuple(dict.fromkeys((*services, *reasoning_services))),
            release_aware=intent_profile.intent.value == "release_awareness",
        )

    def _filter_debug(self, filters: VectorSearchFilters) -> dict[str, list[str] | str | bool | None]:
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

    def _chunk_diversity(self, results: list[tuple[object, float]]) -> dict[str, int]:
        diversity: dict[str, int] = {}
        for chunk, _score in results:
            domain = str(chunk.metadata.get("service_domain") or "unknown")
            diversity[domain] = diversity.get(domain, 0) + 1
        return dict(sorted(diversity.items()))

    def _debug_requested(self, request_debug: bool | None) -> bool:
        return self.debug_enabled if request_debug is None else bool(request_debug or self.debug_enabled)

    def _select_final_chunks(
        self,
        reranked: list[tuple[object, float]],
        *,
        mapped_services: tuple[str, ...],
        pattern_services: tuple[str, ...],
        intent: str | None = None,
    ) -> list[tuple[object, float]]:
        selected: list[tuple[object, float]] = []
        selected_ids: set[str] = set()

        for service in (
            *self._prioritized_mapped_services(mapped_services, intent=intent),
            *pattern_services,
            *self._intent_critical_services(intent),
        ):
            for chunk, score in reranked:
                if chunk.id in selected_ids:
                    continue
                if str(chunk.metadata.get("service", "")).lower() == service.lower():
                    selected.append((chunk, score))
                    selected_ids.add(chunk.id)
                    break
            if len(selected) >= self.top_k:
                break

        for domain in self._diversity_domains(intent):
            if len(selected) >= self.top_k:
                break
            if any(str(chunk.metadata.get("service_domain", "")).lower() == domain for chunk, _score in selected):
                continue
            for chunk, score in reranked:
                if chunk.id in selected_ids:
                    continue
                if str(chunk.metadata.get("service_domain", "")).lower() == domain:
                    selected.append((chunk, score))
                    selected_ids.add(chunk.id)
                    break

        for chunk, score in reranked:
            if len(selected) >= self.top_k:
                break
            if chunk.id in selected_ids:
                continue
            selected.append((chunk, score))
            selected_ids.add(chunk.id)
        return selected

    def _explicit_query_services(self, question: str) -> tuple[str, ...]:
        normalized_question = question.lower()
        return tuple(
            service
            for service, terms in SERVICE_QUERY_TERMS.items()
            if any(term in normalized_question for term in terms)
        )

    def _prioritized_mapped_services(self, mapped_services: tuple[str, ...], intent: str | None = None) -> tuple[str, ...]:
        priority_by_intent = {
            "security": {
                "Identity and Access Management": 0,
                "Virtual Cloud Network": 1,
                "Vault": 2,
                "Cloud Guard": 3,
                "Audit": 4,
                "Logging": 5,
                "Monitoring": 6,
                "Security Zones": 7,
                "Network Security Groups": 8,
            },
            "dr": {
                "Data Guard": 0,
                "Full Stack Disaster Recovery": 1,
                "DNS": 2,
                "Vault": 3,
                "Logging": 4,
                "Monitoring": 5,
                "Database Services": 6,
                "Object Storage": 7,
            },
        }
        default_priority = {
            "OCI Kubernetes Engine": 0,
            "Database Migration": 1,
            "Load Balancer": 2,
            "Container Registry": 3,
            "Database Services": 4,
            "Autonomous Database": 5,
            "Logging": 6,
            "Monitoring": 7,
            "Identity and Access Management": 8,
            "Vault": 9,
            "Object Storage": 10,
            "Virtual Cloud Network": 11,
            "Cloud Guard": 12,
            "Audit": 13,
        }
        priority = priority_by_intent.get(intent or "", default_priority)
        return tuple(
            sorted(
                mapped_services,
                key=lambda service: (priority.get(service, 100), service),
            )
        )

    def _diversity_domains(self, intent: str | None) -> tuple[str, ...]:
        domains_by_intent = {
            "architecture": ("architecture", "networking", "database", "observability", "security", "cost"),
            "migration": ("containers", "database", "networking", "observability", "security", "cost"),
            "dr": ("resilience", "database", "networking", "observability", "security", "storage"),
            "cost": ("cost", "compute", "storage", "database", "observability", "architecture"),
            "observability": ("observability", "security", "compute", "database", "containers"),
            "security": ("security", "networking", "observability", "database", "architecture"),
            "ai_ml": ("compute", "containers", "storage", "observability", "security", "cost"),
            "saas_platform": ("networking", "containers", "database", "observability", "security", "cost"),
            "analytics": ("storage", "database", "observability", "security", "cost"),
        }
        return domains_by_intent.get(intent or "", ("architecture", "observability", "security", "cost"))

    def _intent_critical_services(self, intent: str | None) -> tuple[str, ...]:
        services_by_intent = {
            "architecture": ("Load Balancer", "Database Services", "Object Storage", "Logging", "Monitoring"),
            "migration": ("OCI Kubernetes Engine", "Container Registry", "Load Balancer", "Database Migration", "Logging", "Monitoring"),
            "dr": ("Database Services", "Logging", "Monitoring", "Object Storage"),
            "cost": ("Compute", "Object Storage", "Cost Management", "Monitoring"),
            "observability": ("Logging", "Monitoring", "Database Services"),
            "security": ("Identity and Access Management", "Virtual Cloud Network", "Vault", "Cloud Guard", "Audit", "Logging", "Monitoring"),
            "ai_ml": ("Compute", "Object Storage", "Logging", "Monitoring"),
            "saas_platform": ("Load Balancer", "Database Services", "Object Storage", "Logging", "Monitoring"),
            "analytics": ("Object Storage", "Database Services", "Logging", "Monitoring"),
        }
        return services_by_intent.get(intent or "", ())

    def _pattern_triggered(self, triggers: tuple[str, ...], text: str) -> bool:
        normalized = text.lower()
        return any(trigger.lower() in normalized for trigger in triggers)

    def _critical_pattern_services(self, pattern_name: str, intent: str | None) -> tuple[str, ...]:
        if intent == "cost":
            return ()
        critical = {
            "highly_available_web_application": ("Load Balancer", "Database Services", "Object Storage", "CDN"),
            "kubernetes_modernization_platform": ("OCI Kubernetes Engine", "Load Balancer", "Logging", "Monitoring"),
            "fintech_disaster_recovery_platform": ("Full Stack Disaster Recovery", "Database Services", "Vault", "Logging", "Monitoring"),
            "ai_inference_platform": ("Compute", "Object Storage", "Logging", "Monitoring"),
            "analytics_data_lake_platform": ("Object Storage", "Database Services", "Logging", "Monitoring"),
            "saas_multi_region_platform": ("Load Balancer", "Database Services", "Object Storage", "Logging", "Monitoring"),
        }
        return critical.get(pattern_name, ())


def build_retriever(settings: Settings, top_k: int = 6) -> OciKnowledgeRetriever:
    embedder: Embedder
    if settings.embedding_provider == "oci_genai":
        if not settings.oci_genai_compartment_id or not settings.oci_genai_embedding_model_id:
            if settings.embedding_fallback_enabled:
                missing = [
                    name
                    for name, value in (
                        ("OCI_GENAI_COMPARTMENT_ID", settings.oci_genai_compartment_id),
                        ("OCI_GENAI_EMBEDDING_MODEL_ID", settings.oci_genai_embedding_model_id),
                    )
                    if not value
                ]
                embedder = FallbackEmbedder(
                    primary=None,
                    fallback=LocalHashingEmbedder(),
                    activation_error="Missing required OCI GenAI embedding setting(s): " + ", ".join(missing),
                )
            else:
                raise ValueError(
                    "OCI_GENAI_COMPARTMENT_ID and OCI_GENAI_EMBEDDING_MODEL_ID are required "
                    "when EMBEDDING_PROVIDER=oci_genai."
                )
        else:
            primary = OciGenerativeAiEmbedder(
                OciGenerativeAiEmbeddingConfig(
                    region=settings.oci_region,
                    profile=settings.oci_profile,
                    auth_mode=settings.oci_auth_mode,
                    compartment_id=settings.oci_genai_compartment_id,
                    model_id=settings.oci_genai_embedding_model_id,
                    endpoint=settings.oci_genai_endpoint,
                    expected_dimensions=settings.oci_genai_embedding_dimensions,
                )
            )
            embedder = (
                FallbackEmbedder(primary=primary, fallback=LocalHashingEmbedder())
                if settings.embedding_fallback_enabled
                else primary
            )
    else:
        embedder = LocalHashingEmbedder()

    if settings.embedding_provider == "oci_genai" and not settings.embedding_fallback_enabled:
        if not settings.oci_genai_compartment_id or not settings.oci_genai_embedding_model_id:
            raise ValueError(
                "OCI_GENAI_COMPARTMENT_ID and OCI_GENAI_EMBEDDING_MODEL_ID are required "
                "when EMBEDDING_PROVIDER=oci_genai."
            )

    if settings.retrieval_provider == "oci_object_storage":
        missing = [
            name
            for name, value in (
                ("OCI_OBJECT_STORAGE_NAMESPACE", settings.oci_object_storage_namespace),
                ("OCI_VECTOR_BUCKET", settings.oci_vector_bucket),
            )
            if not value
        ]
        if missing and not settings.retrieval_fallback_enabled:
            raise ValueError(
                "OCI_OBJECT_STORAGE_NAMESPACE and OCI_VECTOR_BUCKET are required "
                "when RETRIEVAL_PROVIDER=oci_object_storage."
            )
        if missing:
            primary_store: VectorStore = UnavailableVectorStore(
                provider_name="oci_object_storage_vector_manifest",
                reason="Missing required OCI Object Storage retrieval setting(s): " + ", ".join(missing),
                missing_config=missing,
            )
        else:
            primary_store = OciObjectStorageVectorStore(
                OciObjectStorageVectorConfig(
                    namespace=settings.oci_object_storage_namespace or "",
                    bucket_name=settings.oci_vector_bucket or "",
                    object_name=settings.oci_vector_object_name,
                    region=settings.oci_region,
                    profile=settings.oci_profile,
                    auth_mode=settings.oci_auth_mode,
                )
            )
        store = (
            FallbackVectorStore(
                primary=primary_store,
                fallback=JsonVectorStore(index_path=settings.knowledge_index_path),
                provider_name="oci_object_storage",
            )
            if settings.retrieval_fallback_enabled
            else primary_store
        )
        provider_name = "oci_object_storage"
    elif settings.retrieval_provider == "oracle_ai_vector_search":
        oracle_store = OracleAiVectorSearchStore(
            OracleAiVectorSearchConfig(
                dsn=settings.oci_vector_db_dsn,
                username=settings.oci_vector_db_user,
                password=settings.oci_vector_db_password,
                wallet_location=settings.oci_vector_wallet_location,
                wallet_password=settings.oci_vector_wallet_password,
                table_name=settings.oci_vector_table_name,
                index_name=settings.oci_vector_index_name or "OCI_ARCH_CHUNKS_VEC_IDX",
                dimensions=settings.oci_vector_dimensions,
                distance_metric=settings.oci_vector_distance_metric,
            )
        )
        store = (
            FallbackVectorStore(
                primary=oracle_store,
                fallback=JsonVectorStore(index_path=settings.knowledge_index_path),
                provider_name="oracle_ai_vector_search",
            )
            if settings.retrieval_fallback_enabled
            else oracle_store
        )
        provider_name = "oracle_ai_vector_search"
    else:
        store = JsonVectorStore(index_path=settings.knowledge_index_path)
        provider_name = "local_json"

    return OciKnowledgeRetriever(
        index_path=settings.knowledge_index_path,
        top_k=top_k,
        embedder=embedder,
        store=store,
        provider_name=provider_name,
        debug_enabled=settings.retrieval_debug_enabled,
        candidate_multiplier=settings.retrieval_candidate_multiplier,
    )


PlaceholderRetriever = OciKnowledgeRetriever


def _metadata_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None
