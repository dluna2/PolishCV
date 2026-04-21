"""ATS package for code-based resume scoring components."""

from .ats_scorer import score_resume_against_job
from .preprocessing import normalize_inputs

__all__ = ["normalize_inputs", "score_resume_against_job"]
