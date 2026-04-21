"""LLM preprocessing agent for resume/job structuring."""

import json
from typing import Any, Dict

from llm_router import generate_response, get_provider_for_stage
from prompts import PREPROCESSING_SYSTEM_PROMPT


def _empty_resume_sections() -> Dict[str, Any]:
    """Return fallback schema with empty values."""
    return {
        "contact": {"name": "", "email": "", "phone": ""},
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
    }


def parse_resume_sections(resume_text: str) -> Dict[str, Any]:
    """Parse raw resume text into structured JSON sections via LLM."""
    user_prompt = (
        "Parse the following resume text.\n\n"
        "Return only JSON. No explanation.\n\n"
        f"Resume Text:\n{resume_text}"
    )

    try:
        provider = get_provider_for_stage("preprocessing")
        raw_output = generate_response(
            provider=provider,
            system_prompt=PREPROCESSING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        parsed = json.loads(raw_output.strip())
        return {
            "contact": parsed.get("contact", {"name": "", "email": "", "phone": ""}),
            "skills": parsed.get("skills", []),
            "experience": parsed.get("experience", []),
            "projects": parsed.get("projects", []),
            "education": parsed.get("education", []),
        }
    except Exception:
        return _empty_resume_sections()


def run_preprocessing_agent(resume_text: str, job_text: str) -> Dict[str, Any]:
    """Backward-compatible entry point; job parsing added later."""
    del job_text
    return {"resume": parse_resume_sections(resume_text)}
