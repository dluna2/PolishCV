"""Code-based ATS scoring module.

No LLM calls should be introduced in this module.
"""

from typing import Any, Dict, List, Tuple

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "will",
    "you",
    "your",
    "we",
    "our",
    "this",
    "these",
    "those",
    "have",
    "has",
    "had",
    "not",
    "but",
}

ACTION_VERBS = {"built", "developed", "designed", "implemented", "improved", "optimized"}
VAGUE_PHRASES = ["helped", "worked on", "assisted"]


def _clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def _tokenize_text(text: str) -> List[str]:
    lowered = text.lower()
    for ch in [".", ",", ";", ":", "!", "?", "(", ")", "[", "]", "{", "}", "/", "\\", "-", "_", "\n", "\t"]:
        lowered = lowered.replace(ch, " ")
    tokens = lowered.split()
    return [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]


def _extract_top_keywords(job_description: str, limit: int = 50) -> List[str]:
    counts: Dict[str, int] = {}
    for token in _tokenize_text(job_description):
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ranked[:limit]]


def _resume_to_text(parsed_resume: Dict[str, Any]) -> str:
    parts: List[str] = []

    contact = parsed_resume.get("contact", {})
    if isinstance(contact, dict):
        parts.extend(str(v) for v in contact.values() if v)

    skills = parsed_resume.get("skills", [])
    if isinstance(skills, list):
        parts.extend(str(s) for s in skills if s)

    for section_name, title_key in [("experience", "role"), ("projects", "name"), ("education", "degree")]:
        section = parsed_resume.get(section_name, [])
        if not isinstance(section, list):
            continue
        for entry in section:
            if not isinstance(entry, dict):
                continue
            if entry.get(title_key):
                parts.append(str(entry[title_key]))
            if entry.get("company"):
                parts.append(str(entry["company"]))
            if entry.get("institution"):
                parts.append(str(entry["institution"]))
            bullets = entry.get("bullets", [])
            if isinstance(bullets, list):
                parts.extend(str(b) for b in bullets if b)

    return " ".join(parts).lower()


def _collect_bullets(parsed_resume: Dict[str, Any]) -> List[str]:
    bullets: List[str] = []
    for section_name in ["experience", "projects"]:
        entries = parsed_resume.get(section_name, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_bullets = entry.get("bullets", [])
            if isinstance(entry_bullets, list):
                bullets.extend(str(b).strip() for b in entry_bullets if str(b).strip())
    return bullets


def _contains_numeric_signal(text: str) -> bool:
    return any(ch.isdigit() for ch in text) or "%" in text or "$" in text


def _compute_action_impact_score(bullets: List[str]) -> Tuple[float, Dict[str, int]]:
    if not bullets:
        return 0.0, {"bullet_count": 0, "action_hits": 0, "impact_hits": 0}

    action_hits = 0
    impact_hits = 0
    for bullet in bullets:
        lower_bullet = bullet.lower()
        if any(verb in lower_bullet for verb in ACTION_VERBS):
            action_hits += 1
        if _contains_numeric_signal(lower_bullet):
            impact_hits += 1

    bullet_count = len(bullets)
    action_ratio = action_hits / bullet_count
    impact_ratio = impact_hits / bullet_count
    score = _clamp_score(((action_ratio * 0.5) + (impact_ratio * 0.5)) * 100.0)
    return score, {"bullet_count": bullet_count, "action_hits": action_hits, "impact_hits": impact_hits}


def _compute_penalty_score(bullets: List[str]) -> Tuple[float, Dict[str, int]]:
    penalty_points = 0
    vague_hits = 0

    normalized_bullets = [b.lower().strip() for b in bullets if b.strip()]
    for bullet in normalized_bullets:
        for phrase in VAGUE_PHRASES:
            if phrase in bullet:
                vague_hits += 1
                penalty_points += 4

    counts: Dict[str, int] = {}
    for bullet in normalized_bullets:
        counts[bullet] = counts.get(bullet, 0) + 1
    repeated_bullets = sum((c - 1) for c in counts.values() if c > 1)
    penalty_points += repeated_bullets * 6

    penalty_score = _clamp_score(100.0 - penalty_points)
    return penalty_score, {"vague_hits": vague_hits, "repeated_bullets": repeated_bullets, "penalty_points": penalty_points}


def compute_ats_score(parsed_resume: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    """Compute deterministic ATS score components from parsed resume and JD text."""
    jd_keywords = _extract_top_keywords(job_description, limit=50)
    resume_text = _resume_to_text(parsed_resume)

    matched_keywords = [kw for kw in jd_keywords if kw in resume_text]
    missing_keywords = [kw for kw in jd_keywords if kw not in resume_text]
    keyword_match_score = _clamp_score(
        (len(matched_keywords) / len(jd_keywords) * 100.0) if jd_keywords else 0.0
    )

    resume_skills = parsed_resume.get("skills", [])
    normalized_skills = {str(skill).lower().strip() for skill in resume_skills if str(skill).strip()} if isinstance(resume_skills, list) else set()
    skill_like_keywords = jd_keywords
    matched_skills = [kw for kw in skill_like_keywords if kw in normalized_skills]
    if not normalized_skills or not skill_like_keywords:
        skills_coverage_score = 0.0
    else:
        skills_coverage_score = _clamp_score((len(matched_skills) / len(skill_like_keywords)) * 100.0)

    present_sections = 0
    for section in ["skills", "experience", "education", "projects"]:
        value = parsed_resume.get(section)
        if isinstance(value, list) and len(value) > 0:
            present_sections += 1
    section_coverage_score = _clamp_score((present_sections / 4.0) * 100.0)

    bullets = _collect_bullets(parsed_resume)
    action_impact_score, action_diag = _compute_action_impact_score(bullets)
    penalty_score, penalty_diag = _compute_penalty_score(bullets)

    overall_score = _clamp_score(
        (keyword_match_score * 0.25)
        + (skills_coverage_score * 0.20)
        + (section_coverage_score * 0.15)
        + (action_impact_score * 0.20)
        + (penalty_score * 0.20)
    )

    return {
        "overall_score": round(overall_score, 2),
        "keyword_match_score": round(keyword_match_score, 2),
        "skills_coverage_score": round(skills_coverage_score, 2),
        "section_coverage_score": round(section_coverage_score, 2),
        "action_impact_score": round(action_impact_score, 2),
        "penalty_score": round(penalty_score, 2),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "diagnostics": {
            "jd_keyword_count": len(jd_keywords),
            "matched_keyword_count": len(matched_keywords),
            "missing_keyword_count": len(missing_keywords),
            "skill_keyword_count": len(skill_like_keywords),
            "matched_skill_count": len(matched_skills),
            "present_sections": present_sections,
            "total_sections": 4,
            **action_diag,
            **penalty_diag,
        },
    }

def score_resume_against_job(structured_resume: Dict[str, Any], structured_job: Dict[str, Any]) -> Dict[str, Any]:
    """Compute ATS-style scoring signals and penalties.

    Intended dimensions include keyword match, skills coverage, section
    coverage, action/impact signals, and penalties.

    Args:
        structured_resume: Parsed/structured resume representation.
        structured_job: Parsed/structured job representation.

    Returns:
        A dictionary with ATS scoring outputs.
    """
    job_description = str(structured_job.get("raw_text", ""))
    return compute_ats_score(structured_resume, job_description)
