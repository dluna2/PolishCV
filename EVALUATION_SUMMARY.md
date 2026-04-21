# PolishCV Evaluation - Quick Reference

## 📋 Summary: Model Evaluation Criteria

You asked for evaluation on **4 criteria** with focus on **model quality**:

| Criterion | Definition | Weight | Current Score* | Target |
|-----------|-----------|--------|---|---|
| **ATS Alignment** | Resume matches JD keywords & ATS structure | 25% | ~3/5 | ≥4/5 |
| **Faithfulness** | No fabricated facts or exaggerated metrics | 25% | ~2/5 ⚠️ | ≥4.5/5 |
| **Relevance** | Feedback directly addresses JD requirements | 25% | ~2.5/5 ⚠️ | ≥4/5 |
| **Clarity** | Feedback is specific & actionable | 25% | ~3/5 | ≥4/5 |

*Estimated based on code review; actual score requires human evaluation dataset

---

## 🚨 Critical Issues (MUST FIX)

### 1️⃣ HALLUCINATION RISK (Severity: CRITICAL)
**Problem:** Tailoring agent can invent metrics not in original resume

**Example:**
- Original: "Optimized database queries"  
- Tailored (bad): "Optimized database queries, achieving 60% latency reduction"
- Issue: "60%" fabricated by LLM

**Current Status:** No protection; prompt says "don't hallucinate" but no enforcement

**Solution:** Implement fact-extraction + diff validation
```python
# Extract metrics/tech/scope from both versions
# Flag any new facts in tailored but not original
# Block changes with high-severity fabrications
```

**Impact:** Prevents resume fraud; critical for user trust

---

### 2️⃣ OPAQUE SCORING (Severity: CRITICAL)
**Problem:** Alignment scores (0-100) vary unpredictably; no explanation

**Example:**
- "Resume: Python experience, JD: Expert Python (5+ years) → Score: 65"
- User: "Is 65 good? Should I apply? Why 65 and not 55?"
- Answer: ??? (No breakdown provided)

**Current Status:** LLM generates score but no rubric shared with LLM

**Solution:** Structured scoring with explicit rubrics + rationales
```python
# For each score dimension, LLM explains:
# - Why this score (0-100)?
# - What matched? What's missing?
# - Risk flags (underqualified, overqualified, tech gap?)
```

**Impact:** User can trust scores and make informed decisions

---

### 3️⃣ GENERIC FEEDBACK (Severity: HIGH)
**Problem:** Feedback could apply to ANY resume; not tailored to JD

**Bad Example:**
```
Strength: "Your experience is solid"
Weakness: "You could improve technical skills"
Fix: "Learn more about the industry"
```

**Good Example:**
```
Strength: "5 years Python aligns with JD requirement"
Weakness: "Missing Apache Spark (JD explicitly requires Spark for data pipelines)"
Fix: "Add Spark project or course; study before interview"
```

**Current Status:** Feedback grounded in ATS + alignment, but often generic

**Solution:** Force feedback to reference specific resume sections + JD quotes
```python
# Each feedback item MUST include:
# - Resume snippet (actual quote)
# - JD requirement (actual quote)
# - Why they matter together
```

**Impact:** Feedback actually useful; user knows what to do

---

### 4️⃣ SILENT FAILURES (Severity: HIGH)
**Problem:** When LLM JSON parsing fails, user gets generic message

**Current:** `"LLM feedback unavailable; using fallback output"` (opaque)

**Better:** `"Error: Invalid JSON from LLM: [error details]. [user action]"` (transparent)

**Solution:** Explicit error reporting with debugging info

**Impact:** Users can tell when something went wrong

---

## 🎯 Root Causes (Why These Problems Exist)

| Issue | Root Cause |
|-------|-----------|
| **Hallucination** | LLM tailoring has no fact-checking; just warned in prompt |
| **Opaque Scoring** | LLM not given explicit rubric; internal inconsistency |
| **Generic Feedback** | Feedback prompt doesn't require JD grounding |
| **Silent Failures** | Exception caught but user not informed |

---

## 🔧 Quick Fix Priority

### Immediate (Week 1)
1. ✅ Add hallucination detection (fact-extraction + diff)
2. ✅ Add explicit error reporting (all agents)

### Soon (Week 2)
3. ✅ Structured scoring with rubrics (alignment agent)
4. ✅ JD-grounded feedback (feedback agent)

### Later (Week 3+)
5. Semantic keyword matching (embeddings)
6. Confidence scores for all outputs
7. Role-specific rubrics

---

## 📊 Evaluation Test Cases Included

I've created **4 test cases** in `evaluation_tests.py`:

1. **TEST_001**: Hallucination - does model fabricate metrics?
2. **TEST_002**: Specificity - does feedback target this JD or generic?
3. **TEST_003**: Actionability - can user implement feedback?
4. **TEST_004**: Semantic Matching - does ATS catch synonyms?

**Run tests:**
```bash
cd /path/to/phase_3
python evaluation_tests.py
```

---

## 📁 Files Created

### 1. `EVALUATION_FRAMEWORK.md` (This explains WHAT to measure)
- 4 evaluation criteria with rubrics (1-5 scales)
- Current model weaknesses by component
- Test cases for each weakness
- Proposed improvements (3 phases)
- Metrics dashboard template

### 2. `MODEL_ISSUES_AND_FIXES.md` (This explains HOW to fix)
- 6 critical issues with concrete solutions
- Code examples for each fix
- UI/UX changes needed
- Implementation roadmap
- Testing approach

### 3. `evaluation_tests.py` (Executable tests)
- Test harness for all 4 criteria
- Hallucination detector
- Specificity checker
- Actionability scorer
- Semantic gap detector
- Run with mock data to see results

---

## 💡 Key Insights

### What PolishCV Does Well ✅
- **Structured pipeline**: Clear stages (preprocessing → ATS → alignment → feedback → tailoring)
- **Cost optimization**: HuggingFace for parsing/alignment, OpenAI for creative feedback/tailoring
- **Defensive prompts**: All prompts include guardrails against hallucination/fabrication
- **Multi-source feedback**: Combines ATS + alignment + prior feedback

### Where It Struggles ❌
- **Hallucination risk**: LLM can invent metrics; no post-hoc validation
- **Transparency**: Scores/feedback opaque; no explanations
- **Generalization**: Feedback often generic; not specific to this JD
- **Error handling**: Failures silent; user never knows something went wrong
- **Keyword matching**: Shallow token matching; misses synonyms

### Model vs Output Quality
- **Model Quality Issues**: Hallucination risk, opaque scoring (internal)
- **Output Quality Issues**: Generic feedback, silent failures (external)
- **Biggest concern**: Hallucination → user risk (fabricated resume)

---

## 🎓 Human Evaluation Rubric (Your Request)

### ATS Alignment (25%)
| 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|
| All keywords included; optimized sections | Most keywords; good structure | Some keywords; adequate structure | Few keywords; weak structure | Critical missing |

**Eval Tip:** Compare keyword match % before/after. Check section formatting.

### Faithfulness (25%)
| 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|
| No invented facts; all preserved | Facts preserved; minor wording | Reordered misleadingly | Facts modified; suspicious metrics | Fabricated |

**Eval Tip:** Look for new metrics, tech, scope claims not in original. Red flags: "40% improvement" without source, new team size, new tools.

### Relevance (25%)
| 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|
| All JD requirements addressed | Most requirements targeted | Some requirements | Few requirements | No JD-specific |

**Eval Tip:** Does feedback mention specific role requirements? Keywords from JD? Or generic?

### Clarity (25%)
| 5 | 4 | 3 | 2 | 1 |
|---|---|---|---|---|
| Specific actions; user knows what to do | Mostly clear guidance | Some clarity; mixed | Vague; hard to implement | Generic platitudes |

**Eval Tip:** Can a real user take action from this? Or does it require interpretation?

---

## 📌 Next Steps

1. **Test the evaluation framework**
   ```bash
   python evaluation_tests.py  # Run mock tests
   ```

2. **Create human evaluation dataset** (50-100 samples)
   - Use test cases from `EVALUATION_FRAMEWORK.md`
   - Score outputs on 4 criteria
   - Identify patterns

3. **Implement fixes** (start with Phase 1)
   - Hallucination detection
   - Error reporting
   - Run tests again

4. **Measure improvement**
   - Track baseline vs. post-fix scores
   - Celebrate wins!

---

## 🤔 Questions to Consider

1. **Hallucination**: What's your risk tolerance? (Zero tolerance vs. rare acceptable)
2. **Generic Feedback**: Do you want AI to propose rewrites or just highlight gaps?
3. **Scope**: Should model prevent application-to-wrong-roles or just warn?
4. **User Trust**: What threshold of errors breaks trust? (>5%? >10%?)

---

## 📞 Support

- **Technical questions**: Check code in agents/ and ats/ folders
- **Evaluation questions**: Refer to `EVALUATION_FRAMEWORK.md`
- **Fix implementation**: Follow `MODEL_ISSUES_AND_FIXES.md`
- **Testing**: Run `evaluation_tests.py`

Good luck! 🚀

