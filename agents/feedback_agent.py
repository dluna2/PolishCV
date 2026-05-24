"""OpenAI feedback agent for strengths, gaps, and emphasis guidance."""

import json
from typing import Any, Dict

from llm_router import generate_response, get_provider_for_stage
from prompts import FEEDBACK_SYSTEM_PROMPT


def _default_feedback_result(summary: str = "LLM feedback unavailable; using fallback output.") -> Dict[str, Any]:
    return {
        "summary": summary,
        "strengths": [],
        "weaknesses": [],
        "priority_fixes": [],
        "suggested_keyword_additions": [],
        "content_to_keep": [],
        "content_to_deprioritize": [],
        "risk_flags": ["feedback_generation_unavailable"],
    }


def _normalize_feedback_json_text(raw_output: str) -> str:
    """Normalize model output into a likely JSON object string."""
    text = (raw_output or "").strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    return text


def generate_feedback(
    parsed_resume: Dict[str, Any],
    job_description: str,
    ats_result: Dict[str, Any],
    alignment_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate strict JSON feedback for downstream tailoring."""
    user_prompt = (
        "Generate strict resume feedback from the provided context.\n"
        "Return JSON only. No explanation.\n\n"
        f"Parsed Resume JSON:\n{json.dumps(parsed_resume, ensure_ascii=True)}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"ATS Result JSON:\n{json.dumps(ats_result, ensure_ascii=True)}\n\n"
        f"Alignment Result JSON:\n{json.dumps(alignment_result, ensure_ascii=True)}"
    )

    try:
        provider = get_provider_for_stage("feedback")
        raw_output = generate_response(
            provider=provider,
            system_prompt=FEEDBACK_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        cleaned_output = _normalize_feedback_json_text(raw_output)
        try:
            parsed = json.loads(cleaned_output)
        except json.JSONDecodeError:
            # Recovery attempt: isolate the first full JSON object in the response.
            start_idx = cleaned_output.find("{")
            end_idx = cleaned_output.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                recovered_output = cleaned_output[start_idx : end_idx + 1]
                parsed = json.loads(recovered_output)
            else:
                raise
        return {
            "summary": parsed.get("summary", ""),
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "priority_fixes": parsed.get("priority_fixes", []),
            "suggested_keyword_additions": parsed.get("suggested_keyword_additions", []),
            "content_to_keep": parsed.get("content_to_keep", []),
            "content_to_deprioritize": parsed.get("content_to_deprioritize", []),
            "risk_flags": parsed.get("risk_flags", []),
        }
    except Exception as exc:
        raw_excerpt = (locals().get("raw_output", "") or "").strip().replace("\n", " ")
        raw_excerpt = raw_excerpt[:300]
        if raw_excerpt:
            print(f"[feedback_agent] JSON parse failed. Raw output excerpt: {raw_excerpt}")
        else:
            print(f"[feedback_agent] Feedback generation failed: {exc}")
        summary = "LLM feedback unavailable; using fallback output."
        if raw_excerpt:
            summary = f"{summary} Raw excerpt: {raw_excerpt}"
        else:
            summary = f"{summary} Exception: {str(exc)[:200]}"
        fallback = _default_feedback_result(summary=summary)
        if raw_excerpt:
            fallback["risk_flags"].append("feedback_json_parse_failed")
        fallback["risk_flags"].append(f"feedback_generation_exception: {str(exc)[:200]}")
        return fallback


def run_feedback_agent(ats_results: Dict[str, Any], alignment_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate actionable feedback using ATS plus alignment outputs."""
    return generate_feedback(
        parsed_resume={},
        job_description="",
        ats_result=ats_results,
        alignment_result=alignment_results,
    )
