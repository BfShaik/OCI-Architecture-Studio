from __future__ import annotations

from dataclasses import dataclass

from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
from oci_arch_studio_backend.services.architecture_patterns import ArchitecturePatternSelector
from oci_arch_studio_backend.services.intents import IntentProfile
from oci_arch_studio_backend.services.response_formatter import STANDARD_RESPONSE_SECTIONS
from oci_arch_studio_backend.services.service_mapping import OciServiceMapper


@dataclass(frozen=True)
class GroundingPrompt:
    system_prompt: str
    user_prompt: str
    sections: tuple[str, ...]
    mapped_services: tuple[str, ...]
    architecture_pattern: str
    estimated_input_tokens: int

    @property
    def prompt_char_count(self) -> int:
        return len(self.system_prompt) + len(self.user_prompt)


class GroundingPromptBuilder:
    """Constructs retrieval-grounded synthesis prompts for OCI GenAI."""

    def build(
        self,
        *,
        question: str,
        workload_context: str | None,
        profile: IntentProfile,
        sources: list[RetrievedSource],
        context_note: str,
    ) -> GroundingPrompt:
        combined_text = " ".join(part for part in (question, workload_context) if part)
        mapping = OciServiceMapper().map_text(combined_text)
        heuristics = ArchitectureHeuristicClassifier().detect(combined_text)
        pattern = ArchitecturePatternSelector().select(
            question=question,
            workload_context=workload_context,
            profile=profile,
            sources=sources,
        )
        sections = (
            "task",
            "intent",
            "mapped_oci_services",
            "workload_domain_profile",
            "architecture_pattern_hints",
            "retrieved_oci_chunks",
            "response_structure",
            "grounding_rules",
        )
        system_prompt = self._system_prompt()
        user_prompt = "\n\n".join(
            (
                "# task\n"
                f"Question: {question}\n"
                f"Workload context: {workload_context or 'not provided'}\n"
                f"Context note: {context_note}",
                "# intent\n"
                f"Detected intent: {profile.intent.value}\n"
                f"Prompt template: {profile.prompt_template}\n"
                f"Focus: {profile.focus}",
                "# mapped_oci_services\n"
                f"{mapping.summary()}\n"
                f"Mapped OCI services: {', '.join(mapping.mapped_services) or 'none detected'}",
                "# workload_domain_profile\n"
                f"Domains: {', '.join(heuristics.domains) or 'none detected'}\n"
                f"Workload types: {', '.join(heuristics.workload_types) or 'none detected'}\n"
                f"Domain guidance: {' '.join(heuristics.recommendations) or 'use retrieved OCI evidence'}",
                "# architecture_pattern_hints\n"
                f"Selected pattern: {pattern.name}\n"
                f"Service priorities: {', '.join(pattern.service_priorities)}\n"
                f"Design moves: {' '.join(pattern.design_moves)}\n"
                f"Known risks: {' '.join(pattern.risks)}",
                "# retrieved_oci_chunks\n" + "\n---\n".join(self._source_block(source) for source in sources[:8]),
                "# response_structure\n"
                + "\n".join(f"{index}. {section}" for index, section in enumerate(STANDARD_RESPONSE_SECTIONS, start=1)),
                "# grounding_rules\n"
                "Use only retrieved OCI chunks and the supplied metadata for service claims. "
                "Prefer architecture-specific recommendations over broad cloud summaries. "
                "State assumptions and evidence gaps instead of inventing missing OCI services. "
                "For migrations, preserve source-to-target mappings and validation/cutover/rollback steps. "
                "For release prompts, do not claim current impact unless release evidence is present. "
                "Return only JSON with keys: answer, recommendations, assumptions, risks, next_steps, quality_warnings.",
            )
        )
        return GroundingPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            sections=sections,
            mapped_services=mapping.mapped_services,
            architecture_pattern=pattern.name,
            estimated_input_tokens=max((len(system_prompt) + len(user_prompt)) // 4, 1),
        )

    def _system_prompt(self) -> str:
        return (
            "You are OCI Architecture Studio, a retrieval-grounded OCI architecture advisor. "
            "Return only valid JSON. Do not expose chain-of-thought. "
            "Use concise architecture reasoning, cite chunk IDs or source titles inside recommendation text where useful, "
            "and keep the answer in the required enterprise architecture sections."
        )

    def _source_block(self, source: RetrievedSource) -> str:
        return "\n".join(
            (
                f"chunk_id: {source.chunk_id}",
                f"title: {source.title}",
                f"source_document: {source.source_url or source.url}",
                f"service: {source.service}",
                f"service_domain: {source.service_domain}",
                f"service_category: {source.service_category or source.category}",
                f"workload_types: {', '.join(source.workload_types)}",
                f"domain_tags: {', '.join(source.domain_tags)}",
                f"architecture_patterns: {', '.join(source.architecture_patterns)}",
                f"migration_mappings: {source.migration_mappings}",
                f"ha_dr_tags: {', '.join(source.ha_dr_tags)}",
                f"cost_optimization_tags: {', '.join(source.cost_optimization_tags)}",
                f"relevance_score: {source.relevance_score}",
                f"stale: {source.is_stale}",
                f"summary: {source.summary[:1400]}",
            )
        )
