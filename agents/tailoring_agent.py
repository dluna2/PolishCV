"""LLM tailoring agent to rewrite resume without inventing facts."""

import json
from typing import Any, Dict

from llm_router import generate_response, get_provider_for_stage
from prompts import TAILORING_SYSTEM_PROMPT


def _default_tailoring_result(original_resume_text: str) -> Dict[str, Any]:
    return {
        "revised_resume_text": original_resume_text,
        "changes_summary": "Tailoring was unavailable; returned original resume text.",
        "keywords_added_or_emphasized": [],
        "content_deemphasized": [],
        "bullet_rewrites": [],
        "truthfulness_warnings": ["Resume was not automatically revised due to unavailable LLM tailoring."],
    }


def tailor_resume(
    parsed_resume: Dict[str, Any],
    original_resume_text: str,
    job_description: str,
    ats_result: Dict[str, Any],
    alignment_result: Dict[str, Any],
    feedback_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Tailor resume text via OpenAI while preserving factual truthfulness."""
    user_prompt = (
        "Tailor the resume using the provided context.\n"
        "Return JSON only. No explanation.\n\n"
        f"Parsed Resume JSON:\n{json.dumps(parsed_resume, ensure_ascii=True)}\n\n"
        f"Original Resume Text:\n{original_resume_text}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"ATS Result JSON:\n{json.dumps(ats_result, ensure_ascii=True)}\n\n"
        f"Alignment Result JSON:\n{json.dumps(alignment_result, ensure_ascii=True)}\n\n"
        f"Feedback Result JSON:\n{json.dumps(feedback_result, ensure_ascii=True)}"
    )

    try:
        provider = get_provider_for_stage("tailoring")
        raw_output = generate_response(
            provider=provider,
            system_prompt=TAILORING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        parsed = json.loads(raw_output.strip())
        return {
            "revised_resume_text": parsed.get("revised_resume_text", original_resume_text),
            "changes_summary": parsed.get("changes_summary", ""),
            "keywords_added_or_emphasized": parsed.get("keywords_added_or_emphasized", []),
            "content_deemphasized": parsed.get("content_deemphasized", []),
            "bullet_rewrites": parsed.get("bullet_rewrites", []),
            "truthfulness_warnings": parsed.get("truthfulness_warnings", []),
        }
    except Exception:
        return _default_tailoring_result(original_resume_text)


def run_tailoring_agent(
    original_resume_text: str,
    structured_resume: Dict[str, Any],
    structured_job: Dict[str, Any],
    ats_results: Dict[str, Any],
    alignment_results: Dict[str, Any],
    feedback_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Produce an honest, improved resume draft from prior outputs."""
    job_description = str(structured_job.get("raw_text", ""))
    return tailor_resume(
        parsed_resume=structured_resume,
        original_resume_text=original_resume_text,
        job_description=job_description,
        ats_result=ats_results,
        alignment_result=alignment_results,
        feedback_result=feedback_results,
    )
