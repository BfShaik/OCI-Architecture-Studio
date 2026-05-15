from __future__ import annotations

import json
from dataclasses import dataclass, field
from time import perf_counter
from typing import Protocol

from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.models.architecture import SynthesisDebugTrace
from oci_arch_studio_backend.services.architecture_heuristics import ArchitectureHeuristicClassifier
from oci_arch_studio_backend.services.grounding_prompt import GroundingPromptBuilder
from oci_arch_studio_backend.services.intents import IntentProfile
from oci_arch_studio_backend.services.response_formatter import (
    ensure_standard_sections,
    format_standard_answer,
)
from oci_arch_studio_backend.services.synthesis_quality import SynthesisQualityScorer


@dataclass(frozen=True)
class SynthesisRequest:
    question: str
    workload_context: str | None
    profile: IntentProfile
    sources: list[RetrievedSource]
    context_note: str
    debug_enabled: bool = False


@dataclass(frozen=True)
class SynthesisResult:
    answer: str
    recommendations: list[str]
    assumptions: list[str]
    risks: list[str]
    next_steps: list[str]
    provider: str
    model: str | None = None
    latency_ms: float | None = None
    warnings: list[str] = field(default_factory=list)
    used_fallback: bool = False
    quality: dict[str, object] | None = None
    debug: SynthesisDebugTrace | None = None


class AdvisorySynthesizer(Protocol):
    provider_name: str

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        ...


class DeterministicAdvisorySynthesizer:
    provider_name = "deterministic"

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        profile = request.profile
        heuristics = ArchitectureHeuristicClassifier().detect(
            " ".join(part for part in (request.question, request.workload_context) if part)
        )
        answer = format_standard_answer(
            profile=profile,
            context_note=request.context_note,
            sources=request.sources,
            workload_context=request.workload_context,
            question=request.question,
        )
        recommendations = [*profile.recommendations, *heuristics.recommendations]
        quality = SynthesisQualityScorer().score(
            answer=answer,
            recommendations=list(recommendations),
            sources=request.sources,
            question=request.question,
        )
        return SynthesisResult(
            answer=answer,
            recommendations=list(recommendations),
            assumptions=list(profile.assumptions),
            risks=list(profile.risks),
            next_steps=list(profile.next_steps),
            provider=self.provider_name,
            model="profile-v0",
            latency_ms=0.0,
            quality=quality.as_dict(),
            debug=self._debug_trace(request, answer) if request.debug_enabled else None,
        )

    def _debug_trace(self, request: SynthesisRequest, answer: str) -> SynthesisDebugTrace:
        return SynthesisDebugTrace(
            selected_provider=self.provider_name,
            selected_model="profile-v0",
            retrieved_chunk_ids=[source.chunk_id or source.title for source in request.sources],
            grounding_prompt_sections=("deterministic_profile", "architecture_pattern", "retrieved_services"),
            prompt_char_count=len(request.question) + len(request.context_note),
            estimated_input_tokens=max((len(request.question) + len(request.context_note)) // 4, 1),
            output_char_count=len(answer),
            fallback_used=False,
        )


@dataclass(frozen=True)
class OciGenAiSynthesisConfig:
    region: str | None
    profile: str
    auth_mode: str
    compartment_id: str
    model_id: str
    endpoint: str | None = None
    max_tokens: int = 1200
    temperature: float = 0.1


class OciGenAiAdvisorySynthesizer:
    provider_name = "oci_genai"

    def __init__(
        self,
        config: OciGenAiSynthesisConfig,
        fallback: AdvisorySynthesizer | None = None,
    ) -> None:
        self.config = config
        self.fallback = fallback or DeterministicAdvisorySynthesizer()
        self._client = None
        self.prompt_builder = GroundingPromptBuilder()
        self._last_grounding_prompt = None
        self._last_token_usage: dict[str, int] = {}

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        started_at = perf_counter()
        try:
            raw_text = self._invoke_model(request)
            payload = self._parse_json(raw_text)
            answer = ensure_standard_sections(
                self._string_or_default(payload.get("answer"), request.context_note),
                profile=request.profile,
                context_note=request.context_note,
            )
            recommendations = self._list_or_default(payload.get("recommendations"), request.profile.recommendations)
            quality = SynthesisQualityScorer().score(
                answer=answer,
                recommendations=recommendations,
                sources=request.sources,
                question=request.question,
            )
            return SynthesisResult(
                answer=answer,
                recommendations=recommendations,
                assumptions=self._list_or_default(payload.get("assumptions"), request.profile.assumptions),
                risks=self._list_or_default(payload.get("risks"), request.profile.risks),
                next_steps=self._list_or_default(payload.get("next_steps"), request.profile.next_steps),
                provider=self.provider_name,
                model=self.config.model_id,
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
                warnings=self._list_or_default(payload.get("quality_warnings"), ()),
                quality=quality.as_dict(),
                debug=self._debug_trace(
                    request=request,
                    output=answer,
                    fallback_used=False,
                    token_usage=self._last_token_usage,
                )
                if request.debug_enabled
                else None,
            )
        except Exception as exc:  # noqa: BLE001 - synthesis must fail closed into deterministic advisory.
            fallback = self.fallback.synthesize(request)
            fallback_reason = f"{type(exc).__name__}: {exc}"
            return SynthesisResult(
                answer=fallback.answer,
                recommendations=fallback.recommendations,
                assumptions=fallback.assumptions,
                risks=fallback.risks,
                next_steps=fallback.next_steps,
                provider=fallback.provider,
                model=fallback.model,
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
                warnings=[
                    "OCI GenAI synthesis failed closed; deterministic synthesis fallback was used.",
                    fallback_reason,
                ],
                used_fallback=True,
                quality=fallback.quality,
                debug=self._debug_trace(
                    request=request,
                    output=fallback.answer,
                    fallback_used=True,
                    fallback_reason=fallback_reason,
                )
                if request.debug_enabled
                else fallback.debug,
            )

    def _invoke_model(self, request: SynthesisRequest) -> str:
        client = self._get_client()
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required for OCI Generative AI synthesis.") from exc

        grounding_prompt = self.prompt_builder.build(
            question=request.question,
            workload_context=request.workload_context,
            profile=request.profile,
            sources=request.sources,
            context_note=request.context_note,
        )
        self._last_grounding_prompt = grounding_prompt
        self._last_token_usage = {}
        serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=self.config.model_id,
        )
        chat_request = oci.generative_ai_inference.models.GenericChatRequest(
            api_format="GENERIC",
            messages=[
                oci.generative_ai_inference.models.SystemMessage(
                    content=[
                        oci.generative_ai_inference.models.TextContent(
                            text=grounding_prompt.system_prompt,
                        )
                    ]
                ),
                oci.generative_ai_inference.models.UserMessage(
                    content=[
                        oci.generative_ai_inference.models.TextContent(
                            text=grounding_prompt.user_prompt,
                        )
                    ]
                ),
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        details = oci.generative_ai_inference.models.ChatDetails(
            compartment_id=self.config.compartment_id,
            serving_mode=serving_mode,
            chat_request=chat_request,
        )
        response = client.chat(details)
        self._last_token_usage = self._extract_usage(response)
        chat_response = getattr(response.data, "chat_response", None)
        return self._extract_text(chat_response)

    def _build_user_prompt(self, request: SynthesisRequest) -> str:
        return self.prompt_builder.build(
            question=request.question,
            workload_context=request.workload_context,
            profile=request.profile,
            sources=request.sources,
            context_note=request.context_note,
        ).user_prompt

    def _get_client(self):
        if self._client is not None:
            return self._client

        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required for OCI Generative AI synthesis.") from exc

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

    def _extract_text(self, chat_response) -> str:
        if chat_response is None:
            raise RuntimeError("OCI GenAI returned no chat response.")
        text = getattr(chat_response, "text", None)
        if text:
            return str(text)
        choices = getattr(chat_response, "choices", None) or []
        if choices:
            message = getattr(choices[0], "message", None)
            content = getattr(message, "content", None) or []
            for item in content:
                item_text = getattr(item, "text", None)
                if item_text:
                    return str(item_text)
        raise RuntimeError("OCI GenAI returned no response text.")

    def _extract_usage(self, response) -> dict[str, int]:
        usage = getattr(getattr(response, "data", None), "usage", None) or getattr(response, "usage", None)
        if usage is None:
            return {}
        values: dict[str, int] = {}
        for source_name, target_name in (
            ("input_tokens", "input_tokens"),
            ("output_tokens", "output_tokens"),
            ("total_tokens", "total_tokens"),
            ("prompt_tokens", "input_tokens"),
            ("completion_tokens", "output_tokens"),
        ):
            value = getattr(usage, source_name, None)
            if isinstance(value, int):
                values[target_name] = value
        return values

    def _debug_trace(
        self,
        *,
        request: SynthesisRequest,
        output: str,
        fallback_used: bool,
        fallback_reason: str | None = None,
        token_usage: dict[str, int] | None = None,
    ) -> SynthesisDebugTrace:
        grounding_prompt = getattr(self, "_last_grounding_prompt", None)
        if grounding_prompt is None:
            grounding_prompt = self.prompt_builder.build(
                question=request.question,
                workload_context=request.workload_context,
                profile=request.profile,
                sources=request.sources,
                context_note=request.context_note,
            )
        return SynthesisDebugTrace(
            selected_provider=self.provider_name if not fallback_used else self.fallback.provider_name,
            selected_model=self.config.model_id if not fallback_used else "profile-v0",
            retrieved_chunk_ids=[source.chunk_id or source.title for source in request.sources],
            grounding_prompt_sections=list(grounding_prompt.sections),
            prompt_char_count=grounding_prompt.prompt_char_count,
            estimated_input_tokens=grounding_prompt.estimated_input_tokens,
            output_char_count=len(output),
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            token_usage=token_usage or {},
        )

    def _parse_json(self, value: str) -> dict[str, object]:
        stripped = value.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.lower().startswith("json"):
                stripped = stripped[4:].strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("OCI GenAI response did not contain a JSON object.")
        return json.loads(stripped[start : end + 1])

    def _string_or_default(self, value: object, default: str) -> str:
        return str(value).strip() if isinstance(value, str) and value.strip() else default

    def _list_or_default(self, value: object, default: tuple[str, ...] | list[str]) -> list[str]:
        if not isinstance(value, list):
            return list(default)
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or list(default)


def build_synthesizer(
    *,
    provider: str,
    region: str | None,
    profile: str,
    auth_mode: str,
    compartment_id: str | None,
    model_id: str | None,
    endpoint: str | None,
    max_tokens: int,
    temperature: float,
) -> AdvisorySynthesizer:
    if provider == "oci_genai":
        if not compartment_id or not model_id:
            raise ValueError(
                "OCI_GENAI_COMPARTMENT_ID and OCI_GENAI_CHAT_MODEL_ID are required "
                "when ADVISORY_SYNTHESIS_PROVIDER=oci_genai."
            )
        return OciGenAiAdvisorySynthesizer(
            OciGenAiSynthesisConfig(
                region=region,
                profile=profile,
                auth_mode=auth_mode,
                compartment_id=compartment_id,
                model_id=model_id,
                endpoint=endpoint,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
    return DeterministicAdvisorySynthesizer()
