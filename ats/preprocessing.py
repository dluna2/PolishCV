"""Code-only preprocessing helpers used by ATS scoring.

This module is for deterministic text cleanup and normalization only.
"""

from typing import Dict


def normalize_inputs(resume_text: str, job_text: str) -> Dict[str, str]:
    """Return normalized input text for ATS scoring.

    Args:
        resume_text: Raw resume text.
        job_text: Raw job description or qualifications text.

    Returns:
        A dictionary containing normalized text fields.
    """
    raise NotImplementedError("ATS preprocessing is not implemented yet.")
