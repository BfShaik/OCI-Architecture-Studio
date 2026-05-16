#!/usr/bin/env python3
"""Standalone OCI Generative AI chat diagnostic.

This script intentionally imports only stdlib and the OCI SDK. It does not
import application code, so it can isolate auth/model/IAM issues from backend
request construction.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import oci


EXIT_AUTH_FAILED = 1
EXIT_MODEL_VISIBILITY_FAILED = 2
EXIT_CHAT_FAILED = 3


def main() -> int:
    args = parse_args()

    print("[STAGE 1] AUTH")
    try:
        client_config, signer, resolved_region = build_auth(args)
        inference_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=client_config,
            signer=signer,
            service_endpoint=args.endpoint,
        )
        print(f"auth ok, region={resolved_region or 'unresolved'}")
    except Exception as exc:  # noqa: BLE001 - diagnostic must report any auth construction failure.
        print_exception(exc)
        return EXIT_AUTH_FAILED

    print("\n[STAGE 2] MODEL VISIBILITY")
    try:
        models = list_active_chat_models(
            client_config=client_config,
            signer=signer,
            compartment_id=args.compartment_id,
        )
        configured_visible = any(getattr(model, "id", None) == args.model_id for model in models)
        print(f"active chat model count={len(models)}")
        print(f"configured model visible={str(configured_visible).lower()}")
        for model in models[:5]:
            print(f"- {getattr(model, 'display_name', '<unknown>')} | {getattr(model, 'id', '<missing-id>')}")
        if not configured_visible:
            print("WARNING: configured --model-id was not found in the active CHAT model list.")
    except Exception as exc:  # noqa: BLE001 - diagnostic must report service/sdk failures.
        print_exception(exc)
        return EXIT_MODEL_VISIBILITY_FAILED

    print("\n[STAGE 3] CHAT INFERENCE")
    try:
        text = chat_hello_world(inference_client, args)
        print(f"response preview={text[:200]}")
        print("chat ok")
    except Exception as exc:  # noqa: BLE001 - diagnostic must report service/sdk failures.
        print_exception(exc)
        return EXIT_CHAT_FAILED

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone OCI GenAI chat hello-world diagnostic.")
    parser.add_argument("--compartment-id", default=os.getenv("OCI_GENAI_COMPARTMENT_ID"))
    parser.add_argument("--model-id", default=os.getenv("OCI_GENAI_CHAT_MODEL_ID"))
    parser.add_argument("--region", default=os.getenv("OCI_REGION"))
    parser.add_argument("--endpoint", default=os.getenv("OCI_GENAI_ENDPOINT"))
    parser.add_argument(
        "--auth-mode",
        default=os.getenv("OCI_AUTH_MODE", "config_file"),
        choices=("config_file", "instance_principal", "resource_principal"),
    )
    parser.add_argument("--profile", default=os.getenv("OCI_PROFILE", "DEFAULT"))
    parser.add_argument("--prompt", default="Say hello in one sentence.")
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("OCI_GENAI_MAX_TOKENS", "64")))
    parser.add_argument("--temperature", type=float, default=float(os.getenv("OCI_GENAI_TEMPERATURE", "0.1")))
    args = parser.parse_args()
    missing = [
        name
        for name, value in (
            ("--compartment-id or OCI_GENAI_COMPARTMENT_ID", args.compartment_id),
            ("--model-id or OCI_GENAI_CHAT_MODEL_ID", args.model_id),
        )
        if not value
    ]
    if missing:
        parser.error("Missing required value(s): " + ", ".join(missing))
    return args


def build_auth(args: argparse.Namespace) -> tuple[dict[str, Any], Any | None, str | None]:
    if args.auth_mode == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        client_config = {"region": args.region} if args.region else {}
        return client_config, signer, args.region
    if args.auth_mode == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        client_config = {"region": args.region} if args.region else {}
        return client_config, signer, args.region

    client_config = oci.config.from_file(profile_name=args.profile)
    if args.region:
        client_config["region"] = args.region
    return client_config, None, client_config.get("region")


def list_active_chat_models(
    *,
    client_config: dict[str, Any],
    signer: Any | None,
    compartment_id: str,
) -> list[Any]:
    management_client = oci.generative_ai.GenerativeAiClient(config=client_config, signer=signer)
    try:
        response = oci.pagination.list_call_get_all_results(
            management_client.list_models,
            compartment_id=compartment_id,
            capability=["CHAT"],
            lifecycle_state="ACTIVE",
        )
        items = list(getattr(response.data, "items", []) or [])
        if not items:
            print("WARNING: capability=CHAT list_models filter returned zero models; retrying unfiltered and filtering locally.")
            items = list_active_models_with_chat_capability(management_client, compartment_id)
    except Exception as exc:
        print("WARNING: capability=CHAT list_models filter failed; retrying unfiltered and filtering locally.")
        print_exception(exc)
        items = list_active_models_with_chat_capability(management_client, compartment_id)
    return items


def list_active_models_with_chat_capability(management_client: Any, compartment_id: str) -> list[Any]:
    response = oci.pagination.list_call_get_all_results(
        management_client.list_models,
        compartment_id=compartment_id,
        lifecycle_state="ACTIVE",
    )
    all_items = list(getattr(response.data, "items", []) or [])
    return [
        model
        for model in all_items
        if "CHAT" in {str(capability) for capability in (getattr(model, "capabilities", None) or [])}
    ]


def chat_hello_world(client: Any, args: argparse.Namespace) -> str:
    serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
        model_id=args.model_id,
    )
    chat_request = oci.generative_ai_inference.models.GenericChatRequest(
        api_format="GENERIC",
        messages=[
            oci.generative_ai_inference.models.SystemMessage(
                content=[
                    oci.generative_ai_inference.models.TextContent(
                        text="You are a concise assistant.",
                    )
                ]
            ),
            oci.generative_ai_inference.models.UserMessage(
                content=[
                    oci.generative_ai_inference.models.TextContent(
                        text=args.prompt,
                    )
                ]
            ),
        ],
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    details = oci.generative_ai_inference.models.ChatDetails(
        compartment_id=args.compartment_id,
        serving_mode=serving_mode,
        chat_request=chat_request,
    )
    response = client.chat(details)
    chat_response = getattr(response.data, "chat_response", None)
    text = extract_text(chat_response)
    if not text:
        raise RuntimeError("OCI GenAI returned no response text.")
    return text


def extract_text(chat_response: Any) -> str:
    if chat_response is None:
        return ""
    text = getattr(chat_response, "text", None)
    if text:
        return str(text)
    choices = getattr(chat_response, "choices", None) or []
    for choice in choices:
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None) or []
        for item in content:
            item_text = getattr(item, "text", None)
            if item_text:
                return str(item_text)
    return ""


def print_exception(exc: Exception) -> None:
    print(f"exception_class={type(exc).__name__}")
    print(f"message={exc}")
    if isinstance(exc, oci.exceptions.ServiceError):
        for attr in ("status", "code", "opc_request_id", "request_id", "target_service"):
            print(f"{attr}={getattr(exc, attr, None)}")


if __name__ == "__main__":
    sys.exit(main())
