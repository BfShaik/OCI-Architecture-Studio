from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol

from oci_arch_studio_backend.models.architecture import RetrievedSource
from oci_arch_studio_backend.services.intents import IntentProfile


@dataclass(frozen=True)
class SynthesisRequest:
    question: str
    workload_context: str | None
    profile: IntentProfile
    sources: list[RetrievedSource]
    context_note: str


@dataclass(frozen=True)
class SynthesisResult:
    answer: str
    recommendations: list[str]
    assumptions: list[str]
    risks: list[str]
    next_steps: list[str]
    provider: str
    model: str | None = None
    warnings: list[str] = field(default_factory=list)
    used_fallback: bool = False


class AdvisorySynthesizer(Protocol):
    provider_name: str

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        ...


class DeterministicAdvisorySynthesizer:
    provider_name = "deterministic"

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        profile = request.profile
        return SynthesisResult(
            answer=(
                f"Intent: {profile.intent.value}. {request.context_note} Use the "
                f"{profile.prompt_template} template to focus the review on "
                f"{profile.focus}."
            ),
            recommendations=list(profile.recommendations),
            assumptions=list(profile.assumptions),
            risks=list(profile.risks),
            next_steps=list(profile.next_steps),
            provider=self.provider_name,
            model="profile-v0",
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

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        try:
            raw_text = self._invoke_model(request)
            payload = self._parse_json(raw_text)
            return SynthesisResult(
                answer=self._string_or_default(payload.get("answer"), request.context_note),
                recommendations=self._list_or_default(payload.get("recommendations"), request.profile.recommendations),
                assumptions=self._list_or_default(payload.get("assumptions"), request.profile.assumptions),
                risks=self._list_or_default(payload.get("risks"), request.profile.risks),
                next_steps=self._list_or_default(payload.get("next_steps"), request.profile.next_steps),
                provider=self.provider_name,
                model=self.config.model_id,
                warnings=self._list_or_default(payload.get("quality_warnings"), ()),
            )
        except Exception as exc:  # noqa: BLE001 - synthesis must fail closed into deterministic advisory.
            fallback = self.fallback.synthesize(request)
            return SynthesisResult(
                answer=fallback.answer,
                recommendations=fallback.recommendations,
                assumptions=fallback.assumptions,
                risks=fallback.risks,
                next_steps=fallback.next_steps,
                provider=fallback.provider,
                model=fallback.model,
                warnings=[
                    "OCI GenAI synthesis failed closed; deterministic synthesis fallback was used.",
                    f"{type(exc).__name__}: {exc}",
                ],
                used_fallback=True,
            )

    def _invoke_model(self, request: SynthesisRequest) -> str:
        client = self._get_client()
        try:
            import oci
        except ImportError as exc:
            raise RuntimeError("OCI SDK is required for OCI Generative AI synthesis.") from exc

        system_prompt = (
            "You are OCI Architecture Studio. Return only JSON with keys: "
            "answer, recommendations, assumptions, risks, next_steps, quality_warnings. "
            "Use only the retrieved OCI evidence. Do not invent OCI services. "
            "Tie actionable recommendations to citation chunk IDs or source titles. "
            "If evidence is insufficient, say so explicitly and keep guidance provisional. "
            "For latest/release prompts, do not claim current impact unless release evidence is present."
        )
        user_prompt = self._build_user_prompt(request)
        serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=self.config.model_id,
        )
        chat_request = oci.generative_ai_inference.models.GenericChatRequest(
            api_format="GENERIC",
            messages=[
                oci.generative_ai_inference.models.SystemMessage(
                    content=[
                        oci.generative_ai_inference.models.TextContent(
                            text=system_prompt,
                        )
                    ]
                ),
                oci.generative_ai_inference.models.UserMessage(
                    content=[
                        oci.generative_ai_inference.models.TextContent(
                            text=user_prompt,
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
        chat_response = getattr(response.data, "chat_response", None)
        return self._extract_text(chat_response)

    def _build_user_prompt(self, request: SynthesisRequest) -> str:
        source_blocks = []
        for source in request.sources[:8]:
            source_blocks.append(
                "\n".join(
                    (
                        f"chunk_id: {source.chunk_id}",
                        f"title: {source.title}",
                        f"service: {source.service}",
                        f"domain: {source.service_domain}",
                        f"stale: {source.is_stale}",
                        f"url: {source.source_url or source.url}",
                        f"summary: {source.summary[:1200]}",
                    )
                )
            )
        return "\n\n".join(
            (
                f"Question: {request.question}",
                f"Workload context: {request.workload_context or 'not provided'}",
                f"Intent: {request.profile.intent.value}",
                f"Prompt template: {request.profile.prompt_template}",
                f"Focus: {request.profile.focus}",
                f"Context note: {request.context_note}",
                "Retrieved evidence:",
                "\n---\n".join(source_blocks),
                "Write enterprise-ready OCI guidance. Keep every recommendation grounded in the evidence.",
            )
        )

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
