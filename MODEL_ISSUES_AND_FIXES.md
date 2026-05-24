# PolishCV - Critical Model Issues & Fixes

## 1. HALLUCINATION PROBLEM (MOST CRITICAL)

### The Issue
The tailoring agent can invent metrics/facts not in the original resume.

**Example:**
```
Original Resume: "Optimized database queries"
Tailored Resume: "Optimized database queries, reducing latency by 60%"

Problem: "60%" never appeared in original resume or user input
Root Cause: LLM infers/extrapolates to match JD requirements
```

### Why It Happens
1. Tailoring prompt says "do not hallucinate" but provides no mechanism
2. LLM sees JD requirement: "quantified impact" 
3. LLM sees vague original: "optimized database queries"
4. LLM decides to invent reasonable number: "60%" (plausible but false)

### Current "Fix" (Ineffective)
```python
# In tailoring_agent.py
"truthfulness_warnings": parsed.get("truthfulness_warnings", [])
```
Problem: Warnings are post-hoc, vague, and user may ignore them.

---

## 2. PROPOSED FIX: FACT-EXTRACTION + DIFF

### Implementation

```python
# new file: fact_validator.py

import re
from typing import Set, List, Tuple

def extract_metrics(text: str) -> Set[str]:
    """
    Extract quantitative metrics from text.
    Returns: {"60%", "$2M", "5 years", "40% improvement", ...}
    """
    metrics = set()
    
    # Percentage patterns
    metrics.update(re.findall(r'\d+%', text))
    
    # Money patterns
    metrics.update(re.findall(r'\$\d+[KMB]?', text))
    
    # Duration patterns
    metrics.update(re.findall(r'\d+\s?(years?|months?|days?|weeks?)', text, re.IGNORECASE))
    
    # Numbers with units
    metrics.update(re.findall(r'\d+[KMB]?\s*(users?|requests?|transactions?|servers?|processes?)', text, re.IGNORECASE))
    
    return metrics


def extract_technologies(text: str) -> Set[str]:
    """
    Extract technology mentions.
    Returns: {"Python", "PostgreSQL", "AWS", "React", ...}
    """
    # Common tech keywords (could extend with ML-based NER)
    tech_keywords = {
        'python', 'javascript', 'java', 'rust', 'go', 'c++', 'typescript',
        'react', 'vue', 'angular', 'django', 'flask', 'spring',
        'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra',
        'aws', 'gcp', 'azure', 'kubernetes', 'docker',
        'apache', 'spark', 'kafka', 'hadoop',
        'tensorflow', 'pytorch', 'scikit-learn',
        'git', 'jenkins', 'gitlab', 'github',
    }
    
    text_lower = text.lower()
    found = set()
    for tech in tech_keywords:
        if re.search(rf'\b{tech}\b', text_lower):
            found.add(tech)
    
    return found


def extract_scope_claims(text: str) -> Set[str]:
    """
    Extract claims about scope (team size, budget, user base, etc).
    Returns: {"led 5-person team", "managed $2M budget", "1M users", ...}
    """
    scope_patterns = [
        r'led\s+(\d+\+?)\s*(?:person|member)?\s*teams?',
        r'managed\s+\$?(\d+[KMB]?)\s*budgets?',
        r'(?:served|reached|supported|handled)\s+(\d+[KMB]?)\s*users?',
        r'(\d+\+?)\s*(?:engineers?|developers?|team\s*members?)\s+direct\s*reports?',
    ]
    
    scope = set()
    for pattern in scope_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        scope.update(matches)
    
    return scope


def validate_tailoring(original_resume: str, tailored_resume: str) -> dict:
    """
    Compare original vs tailored resume for fact fabrication.
    
    Returns:
    {
        "hallucinations": [...],
        "safe": bool,
        "confidence": float,
        "warnings": [...],
        "detailed_diff": {...}
    }
    """
    
    original_metrics = extract_metrics(original_resume)
    tailored_metrics = extract_metrics(tailored_resume)
    fabricated_metrics = tailored_metrics - original_metrics
    
    original_tech = extract_technologies(original_resume)
    tailored_tech = extract_technologies(tailored_resume)
    fabricated_tech = tailored_tech - original_tech
    
    original_scope = extract_scope_claims(original_resume)
    tailored_scope = extract_scope_claims(tailored_resume)
    fabricated_scope = tailored_scope - original_scope
    
    hallucinations = []
    
    # Flag new metrics with HIGH confidence (these are invented)
    for metric in fabricated_metrics:
        hallucinations.append({
            "type": "metric_fabrication",
            "value": metric,
            "severity": "HIGH",
            "example": f"Found '{metric}' in tailored but not original"
        })
    
    # Flag new technologies with MEDIUM confidence (could be valid rephrasing)
    for tech in fabricated_tech:
        hallucinations.append({
            "type": "technology_addition",
            "value": tech,
            "severity": "MEDIUM",
            "example": f"Found '{tech}' in tailored but not original"
        })
    
    # Flag new scope claims with HIGH confidence
    for scope in fabricated_scope:
        hallucinations.append({
            "type": "scope_fabrication",
            "value": scope,
            "severity": "HIGH",
            "example": f"New scope claim: '{scope}'"
        })
    
    high_severity = sum(1 for h in hallucinations if h["severity"] == "HIGH")
    medium_severity = sum(1 for h in hallucinations if h["severity"] == "MEDIUM")
    
    if high_severity > 0:
        safe = False
        confidence = 0.95  # High confidence these are hallucinations
    elif medium_severity > 2:
        safe = False
        confidence = 0.7
    else:
        safe = True
        confidence = 0.95
    
    return {
        "safe": safe,
        "hallucinations": hallucinations,
        "confidence": confidence,
        "high_severity_count": high_severity,
        "medium_severity_count": medium_severity,
        "detailed_diff": {
            "fabricated_metrics": list(fabricated_metrics),
            "fabricated_tech": list(fabricated_tech),
            "fabricated_scope": list(fabricated_scope),
        }
    }
```

### Integration with Tailoring Agent

```python
# modified tailoring_agent.py

from fact_validator import validate_tailoring

def tailor_resume(...) -> Dict[str, Any]:
    """Tailor resume with hallucination detection."""
    
    try:
        provider = get_provider_for_stage("tailoring")
        raw_output = generate_response(...)
        parsed = json.loads(raw_output.strip())
        revised_resume = parsed.get("revised_resume_text", original_resume_text)
        
        # ✅ NEW: Validate for hallucinations
        validation = validate_tailoring(original_resume_text, revised_resume)
        
        if not validation["safe"]:
            # High risk: Return with warnings
            return {
                "revised_resume_text": original_resume_text,  # Keep original
                "changes_summary": "Tailoring blocked due to hallucination risk.",
                "keywords_added_or_emphasized": [],
                "content_deemphasized": [],
                "bullet_rewrites": [],
                "truthfulness_warnings": [
                    f"BLOCKED: {h['type']} detected: {h['example']}"
                    for h in validation["hallucinations"]
                    if h["severity"] == "HIGH"
                ],
                "hallucination_risk": {
                    "detected": True,
                    "confidence": validation["confidence"],
                    "hallucinations": validation["hallucinations"]
                }
            }
        
        return {
            "revised_resume_text": revised_resume,
            "changes_summary": parsed.get("changes_summary", ""),
            "keywords_added_or_emphasized": parsed.get("keywords_added_or_emphasized", []),
            "content_deemphasized": parsed.get("content_deemphasized", []),
            "bullet_rewrites": parsed.get("bullet_rewrites", []),
            "truthfulness_warnings": parsed.get("truthfulness_warnings", []),
            "hallucination_risk": {
                "detected": False,
                "confidence": validation["confidence"],
                "hallucinations": validation["hallucinations"]  # Empty or low-severity only
            }
        }
    
    except Exception:
        return _default_tailoring_result(original_resume_text)
```

### User Interface Change

```python
# In app.py, when displaying tailoring results:

if tailoring_result.get("hallucination_risk", {}).get("detected"):
    st.error("⚠️ Hallucination Risk Detected")
    st.warning(
        "The LLM attempted to add facts not in your original resume. "
        "Showing original resume instead. Blocked changes:"
    )
    for h in tailoring_result["hallucination_risk"]["hallucinations"]:
        if h["severity"] == "HIGH":
            st.write(f"- {h['type']}: {h['example']}")
    st.info("✅ Recommendation: Manually add these metrics if they're true, with proper documentation.")
else:
    # Show revised resume normally
    st.success("Resume tailored successfully")
    st.write(tailoring_result["revised_resume_text"])
```

---

## 3. OPAQUE SCORING (CRITICAL)

### The Issue
Alignment scores (0-100) vary wildly; no explanation; user can't trust them.

**Example:**
```
Resume: "Used Python"
JD: "Expert Python developer (5+ years)"

LLM Score: 65 (no reasoning provided)

User question: Why 65? Is this good? Should I apply?
Answer: ??? (No breakdown provided)
```

### Current Code (No Breakdown)

```python
# In alignment_agent.py
def evaluate_alignment(...):
    return {
        "semantic_relevance_score": 0,  # 0-100 but what does it mean?
        "experience_alignment_score": 0,
        ...
    }
```

### Proposed Fix: Structured Scoring with Justification

```python
# new version of alignment_agent.py

ALIGNMENT_SYSTEM_PROMPT_V2 = """You are a strict resume-job alignment evaluator.

Score on these EXACT dimensions (0-100 each):

1. SEMANTIC_RELEVANCE (Do the skills/tech match?)
   - 100: All required tech/domains present
   - 75: Most required tech present
   - 50: Some relevant skills present
   - 25: Few relevant skills
   - 0: No relevant skills

2. EXPERIENCE_ALIGNMENT (Does experience level match?)
   - 100: Experience level exceeds requirement (senior for mid-level role)
   - 75: Experience level matches requirement
   - 50: Experience level is below but close
   - 25: Experience level significantly below
   - 0: No relevant experience

3. RESPONSIBILITY_MATCH (Do responsibilities match?)
   - 100: Candidate led similar initiatives; scope/impact clear
   - 75: Candidate has relevant responsibilities
   - 50: Some overlapping responsibilities
   - 25: Limited responsibility overlap
   - 0: No matching responsibilities

Return JSON EXACTLY:
{
  "semantic_relevance": {
    "score": <0-100>,
    "rationale": "<1-2 sentences explaining why>",
    "matched_keywords": ["tech1", "tech2"],
    "missing_keywords": ["tech3", "tech4"]
  },
  "experience_alignment": {
    "score": <0-100>,
    "rationale": "<1-2 sentences>",
    "candidate_level": "<entry|mid|senior|lead>",
    "required_level": "<entry|mid|senior|lead>"
  },
  "responsibility_match": {
    "score": <0-100>,
    "rationale": "<1-2 sentences>",
    "matched_responsibilities": ["resp1"],
    "missing_responsibilities": ["resp2"]
  },
  "overall_fit": <average of 3 scores>,
  "risk_flags": ["flag1", "flag2"]  // e.g., "overqualified", "underqualified", "tech_gap"
}
"""

def evaluate_alignment(parsed_resume, job_description, ats_result):
    """Evaluate alignment with structured scoring."""
    
    try:
        provider = get_provider_for_stage("alignment")
        raw_output = generate_response(
            provider=provider,
            system_prompt=ALIGNMENT_SYSTEM_PROMPT_V2,
            user_prompt=user_prompt,
        )
        parsed = json.loads(raw_output.strip())
        
        return {
            "semantic_relevance_score": parsed["semantic_relevance"]["score"],
            "semantic_relevance_rationale": parsed["semantic_relevance"]["rationale"],
            "semantic_matched_keywords": parsed["semantic_relevance"]["matched_keywords"],
            "semantic_missing_keywords": parsed["semantic_relevance"]["missing_keywords"],
            
            "experience_alignment_score": parsed["experience_alignment"]["score"],
            "experience_alignment_rationale": parsed["experience_alignment"]["rationale"],
            "candidate_level": parsed["experience_alignment"]["candidate_level"],
            "required_level": parsed["experience_alignment"]["required_level"],
            
            "responsibility_match_score": parsed["responsibility_match"]["score"],
            "responsibility_match_rationale": parsed["responsibility_match"]["rationale"],
            "matched_responsibilities": parsed["responsibility_match"]["matched_responsibilities"],
            "missing_responsibilities": parsed["responsibility_match"]["missing_responsibilities"],
            
            "overall_fit": parsed["overall_fit"],
            "risk_flags": parsed.get("risk_flags", []),
        }
    
    except Exception:
        return _default_alignment_result()
```

### UI Update

```python
# In app.py

alignment = alignment_result

st.subheader("📊 Alignment Analysis")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Semantic Relevance",
        f"{alignment['semantic_relevance_score']}/100",
        delta=None
    )
    st.caption(alignment.get("semantic_relevance_rationale", ""))
    st.write("Matched: " + ", ".join(alignment.get("semantic_matched_keywords", [])))

with col2:
    st.metric(
        "Experience Level",
        f"{alignment['candidate_level'].title()}",
        delta=f"(need: {alignment['required_level'].title()})"
    )
    st.caption(alignment.get("experience_alignment_rationale", ""))

with col3:
    st.metric(
        "Responsibility Match",
        f"{alignment['responsibility_match_score']}/100",
        delta=None
    )

if alignment.get("risk_flags"):
    st.warning("⚠️ Alignment Risks:")
    for flag in alignment["risk_flags"]:
        st.write(f"- {flag}")
```

---

## 4. SILENT FAILURES (HIGH PRIORITY)

### The Issue
When LLM returns invalid JSON, user gets generic fallback with no indication of failure.

```python
# Current code
try:
    parsed = json.loads(raw_output.strip())
except Exception:
    return _default_feedback_result(summary="LLM feedback unavailable")
    # User sees: "LLM feedback unavailable; using fallback output."
    # But can't tell what went wrong
```

### Proposed Fix: Detailed Error Reporting

```python
# in feedback_agent.py

def generate_feedback(...) -> Dict[str, Any]:
    """Generate feedback with explicit error reporting."""
    
    try:
        provider = get_provider_for_stage("feedback")
        raw_output = generate_response(...)
        
        cleaned_output = _normalize_feedback_json_text(raw_output)
        
        try:
            parsed = json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            # Attempt recovery
            start_idx = cleaned_output.find("{")
            end_idx = cleaned_output.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    recovered_output = cleaned_output[start_idx : end_idx + 1]
                    parsed = json.loads(recovered_output)
                    # Recovery succeeded, continue
                except json.JSONDecodeError:
                    # Recovery failed
                    return {
                        "status": "error",
                        "error_type": "json_parse_failure",
                        "error_message": f"Invalid JSON from LLM: {str(e)[:200]}",
                        "raw_output_excerpt": cleaned_output[:500],
                        "user_action": "Please try again or contact support",
                        "fallback_feedback": _default_feedback_result()
                    }
        
        return {
            "status": "success",
            "summary": parsed.get("summary", ""),
            "strengths": parsed.get("strengths", []),
            # ... rest of fields
        }
    
    except Exception as exc:
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
            "user_action": "Please contact support with error details",
            "fallback_feedback": _default_feedback_result()
        }
```

### UI Update

```python
# In app.py

feedback_result = generate_feedback(...)

if feedback_result.get("status") == "error":
    st.error(f"⚠️ Error: {feedback_result['error_type']}")
    st.write(f"Details: {feedback_result['error_message']}")
    st.info(f"Action: {feedback_result['user_action']}")
    
    # Show whatever we could extract
    if feedback_result.get("raw_output_excerpt"):
        with st.expander("Raw Output (Debug)"):
            st.code(feedback_result["raw_output_excerpt"])
else:
    # Normal display
    st.success("Feedback generated successfully")
    # ... display feedback
```

---

## 5. GENERIC FEEDBACK (HIGH PRIORITY)

### The Issue
Feedback could apply to any resume; doesn't address specific gaps from JD.

**Generic (Bad):**
```
Strengths: Your experience is solid
Weaknesses: You could improve technical skills
Priority Fix: Learn more about the industry
```

**Specific (Good):**
```
Strengths: 5 years Python experience aligns with requirement
Weaknesses: Missing Apache Spark; JD requires Spark for data pipeline work
Priority Fix: Add Spark project or course; if no real experience, study up before interview
```

### Solution: Grounding Prompt in JD Analysis

```python
FEEDBACK_SYSTEM_PROMPT_V2 = """You are a strict, JD-grounded resume feedback reviewer.

CRITICAL: Every feedback item MUST reference:
- A specific resume section (e.g., "experience[0].bullets[2]")
- A specific JD requirement (quote it)
- Actionable fix

Feedback template:
{
  "summary": "<1-2 sentences on overall fit>",
  "strengths": [
    {
      "item": "<specific strength>",
      "evidence": {
        "resume_snippet": "<actual quote from resume>",
        "jd_requirement": "<actual quote from JD>",
        "why_strong": "<how they align>"
      }
    }
  ],
  "weaknesses": [
    {
      "item": "<specific gap>",
      "evidence": {
        "resume_section": "<where it should be but isn't>",
        "jd_requirement": "<what JD asks for>",
        "impact": "<why this gap matters for the role>"
      }
    }
  ],
  "priority_fixes": [
    {
      "fix": "<concrete change>",
      "why_priority": "<tied to JD requirement>",
      "action": "<exactly what user should do>",
      "effort": "<quick|medium|hard>"
    }
  ],
  "risk_flags": []
}

Rules:
- GROUND EVERYTHING in JD
- Do not give generic career advice
- If resume doesn't address a major JD requirement, flag it
- If resume exceeds requirements, note it as strength
"""

def generate_feedback(...):
    """Generate JD-grounded feedback with evidence."""
    
    # First, extract JD requirements
    jd_requirements = extract_jd_requirements(job_description)
    
    user_prompt = (
        "Generate strict, JD-grounded resume feedback.\n\n"
        f"JD REQUIREMENTS IDENTIFIED:\n"
        + "\n".join([f"- {req}" for req in jd_requirements]) + "\n\n"
        f"Parsed Resume JSON:\n{json.dumps(parsed_resume, ensure_ascii=True)}\n\n"
        f"Full Job Description:\n{job_description}\n\n"
        f"ATS Result:\n{json.dumps(ats_result, ensure_ascii=True)}\n\n"
        f"Alignment Result:\n{json.dumps(alignment_result, ensure_ascii=True)}"
    )
    
    # ... generate and parse
```

---

## 6. IMPLEMENTATION ROADMAP

### Phase 1: Safety (Week 1-2) - MUST DO
- [ ] Fact validator (hallucination detection)
- [ ] Integrate with tailoring agent
- [ ] Explicit error reporting in all agents
- [ ] UI changes to surface errors

### Phase 2: Quality (Week 3-4) - HIGH PRIORITY
- [ ] Structured alignment scoring with rationales
- [ ] JD requirement extraction
- [ ] Ground feedback in JD (no generic advice)
- [ ] Add confidence scores to all outputs

### Phase 3: Intelligence (Week 5-6) - NICE TO HAVE
- [ ] Semantic keyword matching (embeddings)
- [ ] Extract dates, competency levels
- [ ] Role-specific evaluation rubrics
- [ ] Feedback prioritization by impact

---

## 7. TESTING THESE FIXES

```python
# test_hallucination_blocker.py
def test_fact_validator_detects_metric_fabrication():
    original = "Optimized database queries"
    tailored = "Optimized database queries, achieving 60% latency reduction"
    
    result = validate_tailoring(original, tailored)
    
    assert not result["safe"]
    assert any(h["value"] == "60%" for h in result["hallucinations"])

def test_error_reporting_explicit():
    # Force JSON parse error
    mock_invalid_json = "{ invalid json }"
    
    result = json.loads(mock_invalid_json)  # Would fail
    # After fix: Should return {"status": "error", ...}
    
    assert result["status"] == "error"
    assert "json_parse_failure" in result["error_type"]

def test_feedback_is_jd_grounded():
    # Check each feedback item has evidence field
    feedback = generate_feedback(...)
    
    for weakness in feedback.get("weaknesses", []):
        assert "evidence" in weakness
        assert "jd_requirement" in weakness["evidence"]
        assert "resume_section" in weakness["evidence"]
```

