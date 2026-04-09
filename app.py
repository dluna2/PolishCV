# Streamlit skeleton app for the PolishCV project

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import streamlit as st


# Basic page setup

st.set_page_config(
    page_title="PolishCV",
    page_icon="📄",
    layout="wide"
)


# Placeholder configuration
MODEL_OPTIONS = {
    "qwen": "Qwen placeholder",
    "llama": "Llama placeholder"
}

SUPPORTED_TASKS = {
    "resume_feedback": "Resume Feedback",
    "resume_tailor": "Resume Tailoring"
}

MIN_RESUME_CHARS = 100
MIN_JOB_DESCRIPTION_CHARS = 100
MAX_INPUT_CHARS = 12000


# Utility helpers
# Replace with notebook functions later if desired

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def validate_inputs(resume_text: str, job_description: str) -> Dict[str, Any]:
    errors: List[str] = []

    if not resume_text.strip():
        errors.append("Resume text is required.")
    if not job_description.strip():
        errors.append("Job description is required.")

    if resume_text and len(resume_text) < MIN_RESUME_CHARS:
        errors.append(f"Resume text must be at least {MIN_RESUME_CHARS} characters.")
    if job_description and len(job_description) < MIN_JOB_DESCRIPTION_CHARS:
        errors.append(
            f"Job description must be at least {MIN_JOB_DESCRIPTION_CHARS} characters."
        )

    if len(resume_text) > MAX_INPUT_CHARS:
        errors.append(f"Resume text must be under {MAX_INPUT_CHARS} characters.")
    if len(job_description) > MAX_INPUT_CHARS:
        errors.append(f"Job description must be under {MAX_INPUT_CHARS} characters.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def score_band(score: float) -> str:
    if score >= 80:
        return "Excellent / Strong match"
    if score >= 60:
        return "Good / Moderate match"
    return "Weak match"


def compute_ats_score(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Placeholder ATS scoring.
    Replace this with your real scoring logic from the notebook.
    """
    resume_words = set(clean_text(resume_text).lower().split())
    jd_words = set(clean_text(job_description).lower().split())

    if not jd_words:
        overall = 0.0
    else:
        overlap = len(resume_words.intersection(jd_words))
        overall = min(round((overlap / max(len(jd_words), 1)) * 100, 2), 100.0)

    return {
        "overall_score": overall,
        "keyword_overlap_score": overall,
        "tech_keyword_score": overall,
        "action_verb_score": 50.0,
        "section_coverage_score": 50.0,
        "important_jd_keywords": sorted(list(jd_words))[:20]
    }


def compare_scores(original_resume: str, revised_resume: str, job_description: str) -> Dict[str, Any]:
    before = compute_ats_score(original_resume, job_description)
    after = compute_ats_score(revised_resume, job_description)

    return {
        "before": before,
        "after": after,
        "score_delta": round(after["overall_score"] - before["overall_score"], 2)
    }


# ------------------------------------------------------------
# Prompt builders
# Replace with your real notebook prompt functions later
# ------------------------------------------------------------
def build_system_instruction() -> str:
    return """
You are an experienced technical recruiter and resume reviewer focused on entry-level software engineering roles.

Important rules:
1. Do not invent facts.
2. Do not add new companies, job titles, dates, certifications, or metrics unless provided.
3. Tailor suggestions only to the given job description.
4. Prefer clear, ATS-friendly language.
5. Explain suggestions so a human can review them.
""".strip()


def build_output_format_instruction() -> str:
    return """
Return valid JSON with:
{
  "summary": "",
  "rewritten_experience": [],
  "missing_keywords": [],
  "feedback": [],
  "gap_suggestions": [],
  "risk_flags": []
}
Return JSON only.
""".strip()


def build_prompt(task_name: str, resume_text: str, job_description: str) -> str:
    system_instruction = build_system_instruction()
    output_instruction = build_output_format_instruction()

    if task_name == "resume_feedback":
        task_block = """
Task:
Review the user's resume for an entry-level software engineering job.
Identify missing keywords, weak wording, and improvement suggestions.
""".strip()
    elif task_name == "resume_tailor":
        task_block = """
Task:
Tailor the user's resume for an entry-level software engineering role.
Rewrite parts of the resume to better align with the job description
without inventing experience.
""".strip()
    else:
        raise ValueError(f"Unsupported task_name: {task_name}")

    return f"""
{system_instruction}

{task_block}

Resume:
{resume_text}

Target Job Description:
{job_description}

{output_instruction}
""".strip()


# ------------------------------------------------------------
# Model inference placeholders
# Replace with your real Hugging Face / API logic later
# ------------------------------------------------------------
def run_qwen(prompt: str) -> Dict[str, Any]:
    """
    Placeholder Qwen response.
    Replace with your real API call.
    """
    fake_output = {
        "summary": "This resume has a reasonable base but needs stronger software engineering alignment.",
        "rewritten_experience": [
            "Built and tested Python-based projects with a focus on clean code and debugging.",
            "Collaborated on software development assignments using Git and agile-style teamwork."
        ],
        "missing_keywords": ["REST API", "SQL", "debugging", "data structures"],
        "feedback": [
            "Add more concrete software engineering keywords from the job description.",
            "Use stronger action verbs and clearer technical impact."
        ],
        "gap_suggestions": [
            "Add one personal or class project involving APIs or databases."
        ],
        "risk_flags": [
            "Review rewritten bullets to ensure they match your real experience."
        ]
    }

    return {
        "success": True,
        "model_id": MODEL_OPTIONS["qwen"],
        "raw_text": json.dumps(fake_output),
        "latency_seconds": 0.25,
        "error": None
    }


def run_llama(prompt: str) -> Dict[str, Any]:
    """
    Placeholder Llama response.
    Replace with your real API call.
    """
    fake_output = {
        "summary": "The resume can be improved with stronger technical wording and better keyword coverage.",
        "rewritten_experience": [
            "Developed software projects using Python and version control tools.",
            "Improved project descriptions to emphasize implementation, testing, and collaboration."
        ],
        "missing_keywords": ["Git", "SQL", "APIs", "problem solving"],
        "feedback": [
            "Clarify technical contributions in each project bullet.",
            "Tailor the summary and skills section more directly to the target role."
        ],
        "gap_suggestions": [
            "Consider adding an end-to-end project that demonstrates backend or database work."
        ],
        "risk_flags": [
            "Verify that all suggested wording reflects actual experience."
        ]
    }

    return {
        "success": True,
        "model_id": MODEL_OPTIONS["llama"],
        "raw_text": json.dumps(fake_output),
        "latency_seconds": 0.35,
        "error": None
    }


def run_selected_model(model_name: str, prompt: str) -> Dict[str, Any]:
    model_name = model_name.lower().strip()

    if model_name == "qwen":
        return run_qwen(prompt)
    if model_name == "llama":
        return run_llama(prompt)

    return {
        "success": False,
        "model_id": model_name,
        "raw_text": "",
        "latency_seconds": 0.0,
        "error": f"Unsupported model: {model_name}"
    }


def parse_model_output(raw_output: str) -> Dict[str, Any]:
    """
    Safe parser for model output.
    Works with JSON when available and falls back to plain text.
    """
    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, dict):
            return {
                "summary": parsed.get("summary", ""),
                "rewritten_experience": parsed.get("rewritten_experience", []),
                "missing_keywords": parsed.get("missing_keywords", []),
                "feedback": parsed.get("feedback", []),
                "gap_suggestions": parsed.get("gap_suggestions", []),
                "risk_flags": parsed.get("risk_flags", [])
            }
    except json.JSONDecodeError:
        pass

    return {
        "summary": "",
        "rewritten_experience": [],
        "missing_keywords": [],
        "feedback": [raw_output] if raw_output else [],
        "gap_suggestions": [],
        "risk_flags": []
    }


def get_revised_resume_text(parsed_output: Dict[str, Any], original_resume_text: str) -> str:
    rewritten_experience = parsed_output.get("rewritten_experience", [])
    if isinstance(rewritten_experience, list) and rewritten_experience:
        return "\n".join(str(item).strip() for item in rewritten_experience if str(item).strip())
    return original_resume_text


def run_pipeline(model_name: str, task_name: str, resume_text: str, job_description: str) -> Dict[str, Any]:
    prompt = build_prompt(task_name, resume_text, job_description)
    inference_result = run_selected_model(model_name, prompt)

    if not inference_result["success"]:
        return {
            "success": False,
            "error": inference_result["error"]
        }

    parsed_output = parse_model_output(inference_result["raw_text"])
    revised_resume_text = get_revised_resume_text(parsed_output, resume_text)
    score_comparison = compare_scores(resume_text, revised_resume_text, job_description)

    return {
        "success": True,
        "prompt": prompt,
        "raw_output": inference_result["raw_text"],
        "parsed_output": parsed_output,
        "revised_resume_text": revised_resume_text,
        "score_comparison": score_comparison,
        "latency_seconds": inference_result["latency_seconds"],
        "model_id": inference_result["model_id"]
    }


# ------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------
st.title("PolishCV")
st.caption("AI-powered resume feedback and tailoring for entry-level software engineering roles")

with st.sidebar:
    st.header("Settings")

    selected_model = st.selectbox(
        "Choose a model",
        options=list(MODEL_OPTIONS.keys()),
        format_func=lambda x: x.upper()
    )

    selected_task = st.selectbox(
        "Choose a task",
        options=list(SUPPORTED_TASKS.keys()),
        format_func=lambda x: SUPPORTED_TASKS[x]
    )

    st.markdown("---")
    st.markdown("### Notes")
    st.info(
        "This is a development skeleton. Model API calls, ATS scoring, and output parsing "
        "can be replaced with your final notebook logic later."
    )

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Resume Input")
    resume_text = st.text_area(
        "Paste resume text",
        height=320,
        placeholder="Paste the user's resume here..."
    )

with right_col:
    st.subheader("Job Description Input")
    job_description = st.text_area(
        "Paste target job description",
        height=320,
        placeholder="Paste the software engineering job description here..."
    )

run_button = st.button("Run PolishCV", type="primary")

if run_button:
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(job_description)

    validation = validate_inputs(cleaned_resume, cleaned_jd)

    if not validation["is_valid"]:
        for error in validation["errors"]:
            st.error(error)
    else:
        with st.spinner("Running model and scoring pipeline..."):
            result = run_pipeline(
                model_name=selected_model,
                task_name=selected_task,
                resume_text=cleaned_resume,
                job_description=cleaned_jd
            )

        if not result["success"]:
            st.error(result["error"])
        else:
            score_comparison = result["score_comparison"]
            parsed_output = result["parsed_output"]

            st.success("Run completed.")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            metric_col1.metric(
                "Before ATS Score",
                f"{score_comparison['before']['overall_score']:.2f}"
            )
            metric_col2.metric(
                "After ATS Score",
                f"{score_comparison['after']['overall_score']:.2f}"
            )
            metric_col3.metric(
                "Score Delta",
                f"{score_comparison['score_delta']:.2f}"
            )
            metric_col4.metric(
                "Latency (s)",
                f"{result['latency_seconds']:.2f}"
            )

            st.markdown("### Score Interpretation")
            st.write(
                f"Before: **{score_band(score_comparison['before']['overall_score'])}**  \n"
                f"After: **{score_band(score_comparison['after']['overall_score'])}**"
            )

            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Feedback",
                "Revised Resume",
                "Scores",
                "Raw Output",
                "Prompt"
            ])

            with tab1:
                st.subheader("Summary")
                st.write(parsed_output.get("summary", ""))

                st.subheader("Feedback")
                feedback = parsed_output.get("feedback", [])
                if feedback:
                    for item in feedback:
                        st.write(f"- {item}")
                else:
                    st.write("No feedback returned.")

                st.subheader("Missing Keywords")
                missing_keywords = parsed_output.get("missing_keywords", [])
                if missing_keywords:
                    st.write(", ".join(missing_keywords))
                else:
                    st.write("No missing keywords returned.")

                st.subheader("Gap Suggestions")
                gap_suggestions = parsed_output.get("gap_suggestions", [])
                if gap_suggestions:
                    for item in gap_suggestions:
                        st.write(f"- {item}")
                else:
                    st.write("No gap suggestions returned.")

                st.subheader("Risk Flags")
                risk_flags = parsed_output.get("risk_flags", [])
                if risk_flags:
                    for item in risk_flags:
                        st.warning(item)
                else:
                    st.write("No risk flags returned.")

            with tab2:
                st.subheader("Revised Resume Text")
                st.text_area(
                    "Generated revised text",
                    value=result["revised_resume_text"],
                    height=250
                )

            with tab3:
                st.subheader("Detailed Score Breakdown")
                st.json(score_comparison)

            with tab4:
                st.subheader("Raw Model Output")
                st.code(result["raw_output"], language="json")

            with tab5:
                st.subheader("Prompt Sent to Model")
                st.text_area(
                    "Prompt",
                    value=result["prompt"],
                    height=300
                )

st.markdown("---")
st.caption(
    "Trustworthiness note: Review all AI suggestions before using them. "
    "Do not submit inaccurate or fabricated resume content."
)