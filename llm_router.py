"""Minimal routing helpers for selecting LLM backends."""

import json
import os
from pathlib import Path
from typing import Literal
from urllib import error, request

from dotenv import load_dotenv


load_dotenv(dotenv_path=Path(".env").resolve())


Provider = Literal["huggingface", "openai"]

HF_CHAT_COMPLETIONS_ENDPOINT = "https://router.huggingface.co/v1/chat/completions"
OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"


def get_provider_for_stage(stage: str) -> Provider:
    """Return the configured provider for a pipeline stage."""
    if stage == "preprocessing":
        return "huggingface"
    if stage == "alignment":
        return "huggingface"
    if stage == "feedback":
        return "openai"
    if stage == "tailoring":
        return "openai"
    raise NotImplementedError(f"No provider configured for stage: {stage}")


def generate_response(
    provider: Provider,
    system_prompt: str,
    user_prompt: str,
    model: str = "",
) -> str:
    """Generate a single non-streaming response from the selected provider."""
    if provider == "huggingface":
        hf_token = os.getenv("HF_TOKEN", "")
        hf_model = model or os.getenv("LLAMA_MODEL", "")
        if not hf_token:
            raise RuntimeError("Missing HF_TOKEN for Hugging Face routing.")
        if not hf_model:
            raise RuntimeError("Missing LLAMA_MODEL for Hugging Face routing.")
        payload = {
            "model": hf_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 1200,
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            HF_CHAT_COMPLETIONS_ENDPOINT,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {hf_token}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=90) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Hugging Face HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Hugging Face request failed: {exc.reason}") from exc
        parsed = json.loads(body)
        return str(parsed["choices"][0]["message"]["content"])

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        openai_model = model or os.getenv("OPENAI_MODEL", "")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY for OpenAI routing.")
        if not openai_model:
            raise RuntimeError("Missing OPENAI_MODEL for OpenAI routing.")

        combined_input = (
            f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n"
            f"USER INPUT:\n{user_prompt}"
        )
        payload = {"model": openai_model, "input": combined_input}
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            OPENAI_RESPONSES_ENDPOINT,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=90) as resp:
                body = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI HTTP error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc.reason}") from exc

        parsed = json.loads(body)
        output = parsed.get("output", [])
        for item in output:
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return str(content.get("text", ""))
        if parsed.get("output_text"):
            return str(parsed.get("output_text", ""))
        return ""

    raise NotImplementedError(f"Provider not implemented: {provider}")
