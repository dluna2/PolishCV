"""Minimal Streamlit app for Feedback and Tailoring actions."""

from __future__ import annotations

import re

import streamlit as st

from agents.alignment_agent import evaluate_alignment
from agents.feedback_agent import generate_feedback
from agents.preprocessing_agent import parse_resume_sections
from agents.tailoring_agent import tailor_resume
from ats.ats_scorer import compute_ats_score

MIN_RESUME_CHARS = 100
MIN_JOB_DESCRIPTION_CHARS = 100


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


st.set_page_config(page_title="PolishCV", page_icon="📄", layout="wide")
st.title("PolishCV")
st.caption("Minimal resume workflow: Feedback or Tailoring")

resume_text = st.text_area("Resume Text", height=260, placeholder="Paste resume text")
job_description = st.text_area("Job Description", height=260, placeholder="Paste job description")
selected_action = st.radio("Action", options=["Feedback", "Tailoring"], horizontal=True)
run_button = st.button("Run", type="primary")

if run_button:
    cleaned_resume = clean_text(resume_text)
    cleaned_jd = clean_text(job_description)

    if len(cleaned_resume) < MIN_RESUME_CHARS:
        st.error(f"Resume text must be at least {MIN_RESUME_CHARS} characters.")
    elif len(cleaned_jd) < MIN_JOB_DESCRIPTION_CHARS:
        st.error(f"Job description must be at least {MIN_JOB_DESCRIPTION_CHARS} characters.")
    else:
        with st.spinner("Running pipeline..."):
            try:
                parsed_resume = parse_resume_sections(cleaned_resume)
            except Exception:
                st.error("Could not process the resume text. Please try again.")
                st.stop()

            try:
                ats_result = compute_ats_score(parsed_resume, cleaned_jd)
            except Exception:
                st.error("Could not compute ATS score. Please try again.")
                st.stop()

            try:
                alignment_result = evaluate_alignment(parsed_resume, cleaned_jd, ats_result)
            except Exception:
                st.error("Could not evaluate resume-job alignment. Please try again.")
                st.stop()

            try:
                feedback_result = generate_feedback(
                    parsed_resume=parsed_resume,
                    job_description=cleaned_jd,
                    ats_result=ats_result,
                    alignment_result=alignment_result,
                )
            except Exception:
                st.error("Could not generate feedback. Please try again.")
                st.stop()

            if selected_action == "Feedback":
                st.success("Feedback completed.")
                st.subheader(f"Overall ATS Score: {ats_result.get('overall_score', 0)}")
                st.write(feedback_result.get("summary", ""))

                st.subheader("Strengths")
                for item in feedback_result.get("strengths", []):
                    st.write(f"- {item}")

                st.subheader("Weaknesses")
                for item in feedback_result.get("weaknesses", []):
                    st.write(f"- {item}")

                st.subheader("Priority Fixes")
                for item in feedback_result.get("priority_fixes", []):
                    st.write(f"- {item}")

                st.subheader("Suggested Keyword Additions")
                for item in feedback_result.get("suggested_keyword_additions", []):
                    st.write(f"- {item}")

                st.subheader("Content to Keep")
                for item in feedback_result.get("content_to_keep", []):
                    st.write(f"- {item}")

                st.subheader("Content to Deprioritize")
                for item in feedback_result.get("content_to_deprioritize", []):
                    st.write(f"- {item}")

                st.subheader("Risk Flags")
                for item in feedback_result.get("risk_flags", []):
                    st.write(f"- {item}")
            else:
                try:
                    tailoring_result = tailor_resume(
                        parsed_resume=parsed_resume,
                        original_resume_text=cleaned_resume,
                        job_description=cleaned_jd,
                        ats_result=ats_result,
                        alignment_result=alignment_result,
                        feedback_result=feedback_result,
                    )
                except Exception:
                    st.error("Could not tailor the resume. Please try again.")
                    st.stop()

                st.success("Tailoring completed.")
                st.subheader(f"Overall ATS Score: {ats_result.get('overall_score', 0)}")
                st.write(tailoring_result.get("changes_summary", ""))

                st.subheader("Revised Resume Text")
                st.text_area(
                    "Revised Resume",
                    value=tailoring_result.get("revised_resume_text", cleaned_resume),
                    height=260,
                )

                st.subheader("Keywords Added or Emphasized")
                for item in tailoring_result.get("keywords_added_or_emphasized", []):
                    st.write(f"- {item}")

                st.subheader("Content Deemphasized")
                for item in tailoring_result.get("content_deemphasized", []):
                    st.write(f"- {item}")

                st.subheader("Bullet Rewrites")
                for item in tailoring_result.get("bullet_rewrites", []):
                    original_bullet = item.get("original_bullet", "")
                    revised_bullet = item.get("revised_bullet", "")
                    st.write(f"- Original: {original_bullet}")
                    st.write(f"  Revised: {revised_bullet}")

                st.subheader("Truthfulness Warnings")
                for item in tailoring_result.get("truthfulness_warnings", []):
                    st.write(f"- {item}")