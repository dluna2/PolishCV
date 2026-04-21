"""LLM alignment agent for relevance/fit assessment after ATS scoring."""

import json
from typing import Any, Dict

from llm_router import generate_response, get_provider_for_stage
from prompts import ALIGNMENT_SYSTEM_PROMPT


def _default_alignment_result() -> Dict[str, Any]:
    return {
        "semantic_relevance_score": 0,
        "experience_alignment_score": 0,
        "matched_qualifications": [],
        "missing_alignment_areas": [],
        "irrelevant_content_flags": [],
        "top_strengths": [],
        "top_weaknesses": [],
        "evidence": {
            "rationale": "",
            "resume_snippets": [],
            "jd_snippets": [],
        },
    }


def evaluate_alignment(parsed_resume: Dict[str, Any], job_description: str, ats_result: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate resume-job alignment via Hugging Face chat completions."""
    user_prompt = (
        "Evaluate resume-job alignment using the inputs below.\n"
        "Return only JSON. No explanation.\n\n"
        f"Parsed Resume JSON:\n{json.dumps(parsed_resume, ensure_ascii=True)}\n\n"
        f"Job Description:\n{job_description}\n\n"
        f"ATS Result JSON:\n{json.dumps(ats_result, ensure_ascii=True)}"
    )

    try:
        provider = get_provider_for_stage("alignment")
        raw_output = generate_response(
            provider=provider,
            system_prompt=ALIGNMENT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        parsed = json.loads(raw_output.strip())
        return {
            "semantic_relevance_score": parsed.get("semantic_relevance_score", 0),
            "experience_alignment_score": parsed.get("experience_alignment_score", 0),
            "matched_qualifications": parsed.get("matched_qualifications", []),
            "missing_alignment_areas": parsed.get("missing_alignment_areas", []),
            "irrelevant_content_flags": parsed.get("irrelevant_content_flags", []),
            "top_strengths": parsed.get("top_strengths", []),
            "top_weaknesses": parsed.get("top_weaknesses", []),
            "evidence": parsed.get("evidence", {"rationale": "", "resume_snippets": [], "jd_snippets": []}),
        }
    except Exception:
        return _default_alignment_result()


def run_alignment_agent(
    structured_resume: Dict[str, Any],
    structured_job: Dict[str, Any],
    ats_results: Dict[str, Any],
) -> Dict[str, Any]:
    """Judge true resume-job alignment beyond keyword matching."""
    job_description = str(structured_job.get("raw_text", ""))
    return evaluate_alignment(structured_resume, job_description, ats_results)
