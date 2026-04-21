# PolishCV - Model Evaluation Framework

## Executive Summary
PolishCV is a multi-agent LLM system for resume feedback and tailoring. The pipeline uses a hybrid approach with:
- **Rule-based ATS scoring** (deterministic keyword matching, action verbs, penalties)
- **LLM-based agents** (preprocessing, alignment, feedback, tailoring)
- **Provider routing** (Hugging Face for preprocessing/alignment, OpenAI for feedback/tailoring)

---

## 1. HUMAN EVALUATION RUBRIC

### 1.1 ATS Alignment (Weight: 25%)

**Definition:** How well the resume matches job description keywords, formatting, and structure recognized by ATS systems.

| Score | Criteria |
|-------|----------|
| 5 | Missing keywords included; section structure optimized; keyword density appropriate; no formatting issues |
| 4 | Most keywords included; good section structure; minor spacing/formatting; high match % (>80%) |
| 3 | Some keywords included; adequate structure; average match % (60-80%) |
| 2 | Few keywords included; weak structure; poor formatting; low match % (<60%) |
| 1 | Critical keywords missing; formatting broken; unrecognizable structure |

**Metrics to Track:**
- Keyword match score (from rule-based ATS)
- Section coverage (skills, experience, education, projects)
- Action verb usage (% of bullets with strong verbs)
- Readability penalties (vague phrases, duplicate bullets)

**Model Component:** `ats_scorer.py` (deterministic baseline)

---

### 1.2 Faithfulness to Real Experience (Weight: 25%)

**Definition:** Resume modifications preserve actual facts; no hallucinations, fabrications, or misleading metrics.

| Score | Criteria |
|-------|----------|
| 5 | No invented experience; all metrics/claims verifiable; rewordings preserve original meaning |
| 4 | All facts preserved; minor wording changes only; no suspicious metrics |
| 3 | Facts mostly preserved; minor reordering; some aggressive rephrasing that could mislead |
| 2 | Facts modified or reordered misleadingly; suspicious metric additions; veracity questionable |
| 1 | Fabricated experience; invented metrics; completely dishonest modifications |

**Red Flags to Detect:**
- ❌ Added metrics not in original (e.g., "Improved performance by 40%" without source)
- ❌ Reframed vague achievements as specific outcomes
- ❌ Invented technologies not mentioned in original
- ❌ Exaggerated timelines or scopes
- ✅ Reworded existing bullets for clarity
- ✅ Emphasized existing qualifications
- ✅ Reordered content for relevance

**Model Component:** `tailoring_agent.py` (needs constraint validation)

**Current Issues:**
- No explicit fact-checking mechanism
- LLM may infer/extrapolate metrics
- Prompt warns against hallucination but lacks enforcement

---

### 1.3 Relevance to Job Description (Weight: 25%)

**Definition:** Feedback and tailored resume directly address requirements in the specific job posting.

| Score | Criteria |
|-------|----------|
| 5 | All JD requirements addressed; tailoring directly targets role; no generic advice |
| 4 | Most JD requirements addressed; targeted feedback; some generic elements |
| 3 | Some JD requirements addressed; mixed targeted/generic; partial alignment |
| 2 | Few JD requirements identified; generic feedback; poor alignment |
| 1 | No JD-specific insights; irrelevant feedback; misaligned suggestions |

**Evaluation Checklist:**
- Are suggested keywords from actual JD?
- Are strengths mapped to JD requirements?
- Are gaps real mismatches or generic?
- Does tailoring address specific role requirements?

**Model Components:**
- Alignment agent: `evaluate_alignment()` - semantic relevance scoring
- Feedback agent: `generate_feedback()` - JD-specific priorities
- Tailoring agent: `tailor_resume()` - targeted rewrites

**Current Issues:**
- Alignment scores are opaque (LLM-generated, no breakdown)
- Feedback may generalize instead of targeting
- Tailoring may prioritize ATS over role fit

---

### 1.4 Clarity & Actionability of Feedback (Weight: 25%)

**Definition:** Feedback is specific, understandable, and user can implement recommendations.

| Score | Criteria |
|-------|----------|
| 5 | Specific action items; clear rationale; prior­itized; user knows exactly what to do |
| 4 | Mostly specific; clear guidance; minor ambiguity; implementable |
| 3 | Some actionable items; mixed clarity; requires interpretation |
| 2 | Vague guidance; unclear priorities; hard to implement |
| 1 | Generic platitudes; contradictory; unusable |

**Feedback Components Evaluated:**
- ✅ Strengths: Are they specific to this resume/JD pair?
- ✅ Weaknesses: Are they fixable and prioritized?
- ✅ Priority Fixes: Do they have context and implementation steps?
- ✅ Keyword Suggestions: Are they from JD or generic?
- ✅ Content to Keep: Is it motivated by JD alignment?
- ⚠️ Content to Deprioritize: Actionable or vague?

**Model Component:** `feedback_agent.py`

**Current Issues:**
- Feedback structure rigid but content quality depends on LLM
- No validation that suggestions are actionable
- Keywords may be generic (from ATS) not role-specific
- Rationale not provided to user

---

## 2. MODEL ARCHITECTURE ANALYSIS

### 2.1 Pipeline Flow

```
Resume + JD
   ↓
[1] PREPROCESSING (HF LLM)
   → Parse into JSON: contact, skills, experience, projects, education
   ↓
[2] ATS SCORING (Rule-based, deterministic)
   → Keyword match, skill coverage, section coverage, action impact, penalties
   ↓
[3] ALIGNMENT (HF LLM)
   → Semantic relevance, experience alignment, matched quals, missing areas
   ↓
[4] FEEDBACK (OpenAI LLM)
   → Strengths, weaknesses, priority fixes, keyword suggestions
   ↓
[5] TAILORING (OpenAI LLM)
   → Revised resume, changes summary, keyword changes, warnings
```

### 2.2 Component Strengths

| Component | Strength |
|-----------|----------|
| **ATS Scorer** | Deterministic, reproducible, no API costs, fast |
| **Preprocessing** | Structured output simplifies downstream processing |
| **Alignment Agent** | Captures semantic fit beyond keywords |
| **Feedback Agent** | Multi-source context (ATS + alignment) for holistic view |
| **Tailoring Agent** | Explicitly guards against hallucination (prompt) |
| **Provider Routing** | Optimized cost/performance (HF for structural, OpenAI for creativity) |

### 2.3 Component Weaknesses

#### **ATS Scorer (Rule-based)**
| Issue | Severity | Impact |
|-------|----------|--------|
| Keyword matching is shallow (token-level, no semantic similarity) | HIGH | Misses synonyms, related concepts |
| Doesn't weight keyword importance/frequency from JD | MEDIUM | All keywords treated equally |
| Action verb list is hardcoded, limited | MEDIUM | May miss industry-specific verbs |
| Penalty scoring is arbitrary (4 pts for vague, 6 for duplicate) | MEDIUM | Weights not justified by data |
| No evaluation of formatting/visual ATS factors | LOW | Assumes plain text submission |
| No section-specific keyword analysis | MEDIUM | E.g., skills section vs. bullet points |

**Example:** A JD with "machine learning" and "neural networks" → ATS only matches if resume has exact tokens, misses "deep learning" or "AI"

---

#### **Preprocessing Agent (HF LLM)**
| Issue | Severity | Impact |
|-------|----------|--------|
| Parsing failures fall back to empty schema silently | HIGH | User doesn't know parsing failed |
| LLM may hallucinate contact info if formatted unusually | MEDIUM | Incorrect email/phone in structured data |
| No validation of parsed JSON against input | MEDIUM | Silent data loss if LLM reformats |
| Duplicate skills/bullets not deduplicated | LOW | May inflate keyword match score |
| No extraction of dates, location, or competency levels | MEDIUM | Loses temporal/relevance context |

**Example:** "led team of 5 developers" → LLM might extract skill as "leadership" (implicit) and later feedback recommends highlighting "leadership" as if from resume

---

#### **Alignment Agent (HF LLM)**
| Issue | Severity | Impact |
|-------|----------|--------|
| Scores (0-100) are opaque; no rubric provided to LLM | HIGH | Scores inconsistent across runs |
| No breakdown per job requirement | HIGH | User doesn't know which specific gaps matter |
| LLM may hallucinate matched qualifications not in resume | MEDIUM | False positives in "matched_qualifications" |
| Evidence (resume_snippets, jd_snippets) not validated as real | MEDIUM | May invent/paraphrase quotes |
| No calibration to user's risk tolerance (strict vs. lenient alignment) | MEDIUM | One-size-fits-all severity |

**Example:** JD asks for "5 years Python" but resume says "Python experience" → LLM might score high alignment without catching years mismatch

---

#### **Feedback Agent (OpenAI LLM)**
| Issue | Severity | Impact |
|-------|----------|--------|
| JSON parsing errors have fallback but lose original feedback | HIGH | User gets generic default instead |
| Feedback structure fixed but content quality varies | MEDIUM | Prompts don't guarantee specificity |
| Keyword suggestions may duplicate ATS output (not role-specific) | MEDIUM | User gets generic + role keywords mixed |
| No source attribution (which issue came from alignment vs. ATS?) | MEDIUM | User can't trace recommendations |
| Priorities not explicitly ranked/scored | MEDIUM | "Priority fixes" may not be actually prioritized |
| Strength/weakness lists may include generic advice | HIGH | Low signal-to-noise ratio |

**Example:** Feedback: "Weakness: Not using enough action verbs" (generic) vs. "Weakness: Your 'data analysis' bullets lack metrics while JD emphasizes quantified impact" (specific)

---

#### **Tailoring Agent (OpenAI LLM)**
| Issue | Severity | Impact |
|-------|----------|--------|
| No explicit constraint: don't invent/exaggerate metrics | HIGH | LLM may add "40% improvement" without source |
| No fact-checking against original resume | HIGH | Hallucinations not caught |
| Revised resume may optimize for ATS at cost of authenticity | MEDIUM | Generic + keyword-stuffed over genuine strength |
| Bullet rewrites not compared to originals for factual drift | MEDIUM | User may not notice subtle exaggerations |
| Warnings about truthfulness generic, not specific to changes | MEDIUM | User doesn't know which rewrites are risky |
| No user review step before applying changes | HIGH | Subtle hallucinations go undetected |

**Example:**
- Original: "Optimized database queries"
- LLM Revision: "Optimized database queries, improving query response time by 60%"
- Issue: "60%" not in original, inferred by LLM

---

## 3. IDENTIFIED WEAKNESSES

### Critical Issues (Must Fix)

1. **Hallucination Risk in Tailoring (CRITICAL)**
   - LLM may invent metrics/technologies not in original
   - No fact-checking mechanism
   - "Truthfulness warnings" are post-hoc, not preventive
   - **Fix:** Parse original resume + tailored resume, diff for added/changed facts

2. **Opaque LLM Scoring (CRITICAL)**
   - Alignment scores (0-100) have no rubric, inconsistent
   - Feedback priorities unmarked
   - **Fix:** Provide LLM explicit scoring rubric; ask for brief justification

3. **Generic Feedback Quality (HIGH)**
   - Feedback may apply to any resume, not this specific one
   - Keyword suggestions may be ATS noise, not role-specific
   - **Fix:** Require feedback to reference specific resume sections + JD requirements

4. **Silent Failures (HIGH)**
   - JSON parsing fails → fallback to empty/generic response
   - User doesn't know feedback was unavailable
   - **Fix:** Explicit error messages + partial output even on parse failure

### Medium Issues

5. **Keyword Matching Shallow**
   - No semantic similarity (synonyms, related terms)
   - **Fix:** Add embedding-based keyword matching

6. **Missing Context**
   - No date/duration analysis
   - No location/relocation signals
   - No competency level inference
   - **Fix:** Extend preprocessing agent or post-process

7. **No Feedback Confidence Scores**
   - User doesn't know if alignment is borderline (40%) vs. strong (85%)
   - **Fix:** Add confidence intervals to scores

8. **Tailoring May Over-Optimize ATS**
   - Revised resume may become generic/keyword-stuffed
   - May sacrifice readability for keyword density
   - **Fix:** Explicit constraint to preserve voice/authenticity

### Low Issues

9. **Action Verb List Hardcoded**
   - Limited to 6 verbs; misses industry-specific ones
   - **Fix:** Extract from JD or use industry vocabulary

10. **No A/B Testing Capability**
    - Can't compare original vs. tailored impact
    - **Fix:** Store all outputs for later analysis

---

## 4. EVALUATION TEST CASES

### Test Case 1: Hallucination Detection
**Input:**
- Resume: "Led project to migrate database"
- JD: Expects "PostgreSQL migration with 50% performance gain"

**Expected Feedback:** "Missing quantified impact and specific technology"
**Expected Tailoring:** Rewrites to emphasize migration type, asks user for actual metrics
**Expected Failure:** Tailoring adds "50% performance gain" without asking

**Evaluation Metric:** Does tailored resume differ only in reordering/emphasis, not adding facts?

---

### Test Case 2: Generic vs. Specific Feedback
**Input:**
- Resume: Generic software engineer role
- JD: Specific "Data Engineer with Spark/Kafka" role

**Expected:** Feedback identifies Spark/Kafka as gaps, suggests technical focus
**Expected Failure:** "Improve your technical skills" (generic)

**Evaluation:** Feedback specificity score (0-1)
- 1.0: Mentions Spark, Kafka, data pipeline work
- 0.5: Mentions "big data" or "data engineering"
- 0.0: Generic skill advice

---

### Test Case 3: ATS Keyword Misses
**Input:**
- Resume: "Wrote microservices with REST APIs"
- JD: "RESTful service architecture, gRPC optional"

**Expected:** Keywords identified: [microservices, REST, APIs, service architecture]
**Expected Failure:** Only finds [microservices] due to shallow tokenization

**Evaluation:** Recall/precision of keyword extraction

---

### Test Case 4: Faithfulness Under Pressure
**Input:**
- Resume: "Managed team"
- JD: Wants "Led 10+ person team, $2M budget"

**Expected Tailoring:** "Cannot add specific team size; suggest quantifying if true"
**Expected Failure:** "Led 10-person team, managed $2M budget" (fabricated)

**Evaluation:** Does tailoring preserve ambiguity or fabricate specificity?

---

## 5. PROPOSED IMPROVEMENTS

### Phase 1: Safety (Must Do)

1. **Fact-Checking Module**
   ```python
   def validate_tailoring(original_resume, tailored_resume):
       # Diff extracted facts
       # Flag added/modified metrics
       # Prompt LLM: "Justify each new claim"
   ```

2. **Explicit Error Reporting**
   ```python
   if json_parse_fails:
       return {
           "status": "error",
           "error_message": "LLM response invalid JSON",
           "partial_output": raw_text,
           "user_action": "Please contact support"
       }
   ```

3. **Feedback Specificity Validation**
   ```python
   feedback_item = "Weakness: Not enough action verbs"
   if generic_phrase in feedback_item:
       confidence = "low"  # Flag for review
   ```

### Phase 2: Quality (High Priority)

4. **Semantic Keyword Matching**
   - Use embeddings (e.g., Sentence Transformers)
   - Match "neural networks" ↔ "deep learning"

5. **Structured Feedback with Sources**
   ```json
   {
       "weakness": "Missing quantified impact",
       "resume_section": "experience[0].bullets",
       "jd_requirement": "track record of delivering measurable results",
       "fix": "Add metrics (time saved, % improvement, etc.)"
   }
   ```

6. **Confidence Scores for All Outputs**
   - Alignment scores + confidence intervals
   - Feedback priority + confidence

### Phase 3: Intelligence (Nice to Have)

7. **Extract More Context**
   - Years of experience, gaps, career progression
   - Technical depth vs. breadth
   - Industry/role trajectory

8. **Role-Specific Rubrics**
   - "Data Engineer" vs. "Product Manager" have different ATS factors
   - Custom keyword weights per role type

9. **Feedback Clustering**
   - Group redundant feedback
   - Rank by impact/effort

---

## 6. TESTING FRAMEWORK

### Unit Tests

```python
# test_ats_scorer.py
def test_keyword_matching():
    """Ensure top keywords from JD are extracted"""
    jd = "We need Python, Django, PostgreSQL..."
    keywords = extract_top_keywords(jd)
    assert "python" in keywords
    assert "django" in keywords

# test_hallucination_detection.py
def test_no_metric_fabrication():
    """Tailored resume should not add metrics"""
    original = {"bullets": ["Led project"]}
    tailored = tailor_resume(original, jd)
    
    original_metrics = extract_metrics(original)
    tailored_metrics = extract_metrics(tailored)
    
    assert not (new_metrics := tailored_metrics - original_metrics)
```

### Integration Tests

```python
def test_full_pipeline_hallucination():
    """E2E: Check for fact fabrication"""
    resume = "Managed small team"
    jd = "Need: Led 50+ engineers"
    
    result = run_pipeline(resume, jd)
    tailored = result["tailored_resume"]
    
    # Should NOT add "50+ engineers"
    assert "50" not in tailored
    
    # Should flag as mismatch
    assert "size_mismatch" in result.get("warnings", [])
```

### Human Evaluation Tests

```python
# human_eval.py - Score outputs on 1-5 rubric per criteria
results = {
    "ats_alignment": 4.2,
    "faithfulness": 4.8,
    "relevance": 3.5,
    "clarity": 4.0,
    "overall": 4.1
}
```

---

## 7. METRICS DASHBOARD

Track across 100+ test cases:

| Metric | Current | Target |
|--------|---------|--------|
| Hallucination Rate (%) | ? | < 5% |
| Feedback Specificity (1-5) | ? | ≥ 4.0 |
| Keyword Recall | ? | > 80% |
| User Action Rate (% actionable) | ? | > 85% |
| ATS Score Correlation | ? | > 0.8 vs. actual ATS |
| Error Rate (silent failures) | ? | < 2% |
| Truthfulness Score (human) | ? | ≥ 4.5 |

---

## 8. CONCLUSION

**PolishCV Strengths:**
- Well-structured pipeline with clear stages
- Hybrid approach (rule-based + LLM) balances cost/quality
- Explicit guardrails in prompts

**Key Gaps:**
- No enforcement of hallucination prevention
- Scores/feedback lack transparency
- Generic outputs competing with specific insights
- Silent failures hide problems

**Immediate Actions:**
1. Implement fact-checking module (Phase 1)
2. Add detailed error reporting
3. Create human evaluation rubric dataset (50 samples)
4. Measure baseline performance on 4 criteria
5. Prioritize hallucination fixes over everything

