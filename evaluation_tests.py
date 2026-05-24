"""
Model Evaluation Test Suite for PolishCV
Tests the 4 evaluation criteria: ATS Alignment, Faithfulness, Relevance, Clarity
"""

import json
from typing import Dict, List, Any, Tuple


# ============================================================================
# TEST DATA
# ============================================================================

TEST_CASES = [
    {
        "id": "TEST_001_hallucination_risk",
        "name": "Hallucination Risk: Fabricated Metrics",
        "resume": """
        John Doe
        john@example.com | 555-1234
        
        EXPERIENCE
        Senior Software Engineer | TechCorp | 2020-2023
        - Led migration of legacy monolith to microservices
        - Improved database performance
        - Mentored junior developers
        """,
        "jd": """
        We're looking for a Senior Engineer with:
        - Experience migrating systems to microservices (preferably with 40%+ performance gains)
        - Track record of leading teams (5+ direct reports)
        - PostgreSQL optimization experience
        - AWS or GCP migration projects
        """,
        "evaluation_criteria": {
            "faithfulness": {
                "description": "Does tailored resume add fake metrics?",
                "red_flags": [
                    "40%",  # Not in original
                    "5+ direct reports",  # Only "mentored" in original
                    "PostgreSQL",  # Not in original
                ],
                "expected_behavior": "Should NOT add these; may highlight migration + performance if true",
                "severity": "CRITICAL"
            }
        }
    },
    {
        "id": "TEST_002_generic_feedback",
        "name": "Generic vs Specific Feedback",
        "resume": """
        Jane Smith
        jane@example.com | 555-5678
        
        SKILLS: Python, JavaScript, React, Git
        
        EXPERIENCE
        Software Engineer | DataCo | 2021-Present
        - Built web applications
        - Fixed bugs and improved code quality
        - Worked with team on features
        """,
        "jd": """
        Data Pipeline Engineer
        
        Required:
        - Apache Spark expertise (3+ years)
        - Kafka/streaming architecture design
        - Python for distributed computing
        - PostgreSQL performance tuning
        - Airflow orchestration experience
        
        Nice to have:
        - GCP BigQuery experience
        - Data modeling expertise
        """,
        "evaluation_criteria": {
            "relevance": {
                "description": "Does feedback identify specific gaps (Spark, Kafka)?",
                "generic_bad": [
                    "Improve your technical skills",
                    "Learn more about data",
                    "Consider taking courses"
                ],
                "specific_good": [
                    "Missing Apache Spark expertise (JD requires 3+ years)",
                    "No mention of Kafka or streaming architecture",
                    "PostgreSQL tuning not evident; JD emphasizes performance optimization"
                ],
                "severity": "HIGH"
            }
        }
    },
    {
        "id": "TEST_003_actionability",
        "name": "Feedback Clarity & Actionability",
        "resume": """
        Bob Johnson
        bob@example.com | 555-9999
        
        SKILLS: Java, Spring Boot, SQL
        
        EXPERIENCE
        Backend Engineer | FinTech Inc | 2019-2023
        - Helped optimize payment processing
        - Worked on microservices architecture
        - Fixed critical bugs
        """,
        "jd": """
        Senior Backend Engineer - Payment Systems
        
        We process $10B+ annually. You'll:
        - Design fault-tolerant payment transaction systems
        - Optimize for sub-100ms latency (p99)
        - Lead transaction consistency under failure scenarios
        - Mentor junior engineers on system design
        - Impact: Your code handles >50K transactions/second
        """,
        "evaluation_criteria": {
            "clarity": {
                "description": "Is feedback specific and actionable?",
                "bad_feedback": [
                    "Your experience is good but needs improvement",
                    "Try to highlight more",
                    "Consider emphasizing technical skills"
                ],
                "good_feedback": [
                    {
                        "item": "Priority Fix #1: Quantify payment processing optimization (original: 'helped optimize'; target: add %latency reduction or txn throughput if available)",
                        "action": "Specific change needed",
                        "rationale": "JD emphasizes measurable impact (sub-100ms, 50K txn/s)"
                    },
                    {
                        "item": "Weakness: No evidence of failure scenario design (critical for payment systems)",
                        "action": "Add relevant project if available",
                        "rationale": "JD requires transaction consistency under failures"
                    }
                ],
                "severity": "HIGH"
            }
        }
    },
    {
        "id": "TEST_004_ats_shallow_matching",
        "name": "ATS Keyword Matching: Shallow vs Semantic",
        "resume": """
        Alice Chen
        alice@example.com | 555-0000
        
        SKILLS: Deep learning, Neural networks, Python, TensorFlow
        
        EXPERIENCE
        ML Engineer | AILabs | 2021-Present
        - Implemented convolutional neural networks
        - Fine-tuned large language models
        - Optimized model inference for production
        """,
        "jd": """
        Machine Learning Engineer
        
        Required:
        - Machine learning fundamentals
        - Expertise in transformer models
        - PyTorch or JAX experience
        - Model deployment experience
        
        Nice to have:
        - LLM fine-tuning
        - Inference optimization
        """,
        "evaluation_criteria": {
            "ats_alignment": {
                "description": "Does ATS catch semantic matches?",
                "shallow_misses": [
                    ("Large language models", "Transformer models"),  # Related but different keywords
                    ("Deep learning", "Machine learning"),  # Subset relationship
                    ("TensorFlow", "PyTorch"),  # Competing frameworks
                ],
                "expected_behavior": "Current: May miss; Should: Recognize LLM ⊂ transformer, DL ⊂ ML",
                "severity": "MEDIUM"
            }
        }
    },
]


# ============================================================================
# EVALUATION FUNCTIONS
# ============================================================================

def check_hallucination(original_resume: str, tailored_resume: str, red_flags: List[str]) -> Dict[str, Any]:
    """
    Check if tailored resume adds unsupported claims from red_flags list.
    
    Returns:
    - hallucinated_items: List of red flags found in tailored but not original
    - risk_level: SAFE, LOW_RISK, MEDIUM_RISK, HIGH_RISK, CRITICAL
    """
    original_lower = original_resume.lower()
    tailored_lower = tailored_resume.lower()
    
    hallucinated = []
    for flag in red_flags:
        flag_lower = flag.lower()
        if flag_lower not in original_lower and flag_lower in tailored_lower:
            hallucinated.append(flag)
    
    if len(hallucinated) == 0:
        risk_level = "SAFE"
    elif len(hallucinated) == 1:
        risk_level = "LOW_RISK"
    elif len(hallucinated) <= 3:
        risk_level = "MEDIUM_RISK"
    else:
        risk_level = "HIGH_RISK" if len(hallucinated) <= 5 else "CRITICAL"
    
    return {
        "hallucinated_items": hallucinated,
        "count": len(hallucinated),
        "risk_level": risk_level,
        "safe": len(hallucinated) == 0
    }


def check_feedback_specificity(feedback_text: str, generic_phrases: List[str], 
                               specific_phrases: List[str]) -> Dict[str, Any]:
    """
    Evaluate if feedback is generic or specific.
    
    Returns:
    - specificity_score: 0.0 (all generic) to 1.0 (all specific)
    - generic_count: How many generic phrases found
    - specific_count: How many specific phrases found
    """
    feedback_lower = feedback_text.lower()
    
    generic_found = sum(1 for phrase in generic_phrases if phrase.lower() in feedback_lower)
    specific_found = sum(1 for phrase in specific_phrases if phrase.lower() in feedback_lower)
    
    total = generic_found + specific_found
    specificity = specific_found / total if total > 0 else 0.0
    
    return {
        "specificity_score": round(specificity, 2),
        "generic_count": generic_found,
        "specific_count": specific_found,
        "verdict": "SPECIFIC" if specificity >= 0.7 else "MIXED" if specificity >= 0.3 else "GENERIC"
    }


def check_actionability(feedback_items: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Evaluate feedback items for actionability.
    
    Each item should have:
    - action: Specific change needed (good)
    - rationale: Why this matters (good)
    
    Returns:
    - actionability_score: % of items with both action + rationale
    - missing_action: Items without clear action
    - missing_rationale: Items without clear rationale
    """
    total = len(feedback_items)
    if total == 0:
        return {
            "actionability_score": 0.0,
            "missing_action": [],
            "missing_rationale": [],
            "verdict": "EMPTY_FEEDBACK"
        }
    
    actionable = 0
    missing_action = []
    missing_rationale = []
    
    for i, item in enumerate(feedback_items):
        has_action = "action" in item and item["action"].strip()
        has_rationale = "rationale" in item and item["rationale"].strip()
        
        if not has_action:
            missing_action.append(f"Item {i}: {item.get('item', 'N/A')}")
        if not has_rationale:
            missing_rationale.append(f"Item {i}: {item.get('item', 'N/A')}")
        
        if has_action and has_rationale:
            actionable += 1
    
    return {
        "actionability_score": round(actionable / total, 2),
        "missing_action": missing_action,
        "missing_rationale": missing_rationale,
        "verdict": "ACTIONABLE" if actionable / total >= 0.8 else "PARTIAL" if actionable / total >= 0.5 else "VAGUE"
    }


def check_semantic_gaps(keywords_in_resume: List[str], keywords_in_jd: List[str],
                        semantic_mappings: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    Check if ATS matching accounts for semantic similarity.
    
    semantic_mappings: List of (from_jd, to_resume) synonyms
    
    Returns:
    - semantic_misses: Keywords from JD that have semantic match in resume
    - false_negatives: Count of keyword pairs that should match
    """
    resume_set = {kw.lower() for kw in keywords_in_resume}
    jd_set = {kw.lower() for kw in keywords_in_jd}
    
    direct_matches = resume_set & jd_set
    semantic_misses = []
    
    for jd_kw, resume_kw in semantic_mappings:
        if jd_kw.lower() in jd_set and resume_kw.lower() in resume_set:
            if jd_kw.lower() not in direct_matches:
                semantic_misses.append({
                    "jd_keyword": jd_kw,
                    "resume_keyword": resume_kw,
                    "relationship": "synonym or subset"
                })
    
    return {
        "direct_matches": len(direct_matches),
        "semantic_misses": semantic_misses,
        "false_negatives": len(semantic_misses),
        "semantic_awareness": "NO" if len(semantic_misses) > 0 else "YES"
    }


# ============================================================================
# COMPREHENSIVE EVALUATION
# ============================================================================

def run_evaluation(test_case: Dict[str, Any], model_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full evaluation on a test case.
    
    model_outputs should contain:
    - tailored_resume: str
    - feedback: Dict
    - alignment: Dict
    """
    
    test_id = test_case["id"]
    results = {
        "test_id": test_id,
        "test_name": test_case["name"],
        "scores": {},
        "detailed_results": {}
    }
    
    # ========== FAITHFULNESS EVALUATION ==========
    if "faithfulness" in test_case["evaluation_criteria"]:
        criteria = test_case["evaluation_criteria"]["faithfulness"]
        halluc_check = check_hallucination(
            test_case["resume"],
            model_outputs.get("tailored_resume", ""),
            criteria.get("red_flags", [])
        )
        results["detailed_results"]["faithfulness"] = halluc_check
        results["scores"]["faithfulness"] = 5.0 if halluc_check["safe"] else max(1.0, 5.0 - halluc_check["count"])
    
    # ========== RELEVANCE EVALUATION ==========
    if "relevance" in test_case["evaluation_criteria"]:
        criteria = test_case["evaluation_criteria"]["relevance"]
        feedback_text = json.dumps(model_outputs.get("feedback", {})).lower()
        
        generic_found = sum(1 for phrase in criteria.get("generic_bad", []) if phrase.lower() in feedback_text)
        specific_found = sum(1 for phrase in criteria.get("specific_good", []) if phrase.lower() in feedback_text)
        
        relevance_score = (specific_found / (specific_found + generic_found + 1)) * 5.0
        results["detailed_results"]["relevance"] = {
            "generic_phrases_found": generic_found,
            "specific_phrases_found": specific_found,
            "note": "Should emphasize specific gaps from JD"
        }
        results["scores"]["relevance"] = round(min(5.0, relevance_score), 2)
    
    # ========== CLARITY EVALUATION ==========
    if "clarity" in test_case["evaluation_criteria"]:
        criteria = test_case["evaluation_criteria"]["clarity"]
        good_feedback = criteria.get("good_feedback", [])
        
        actionability = check_actionability(good_feedback) if isinstance(good_feedback, list) else {
            "actionability_score": 0.0,
            "verdict": "NOT_EVALUATED"
        }
        results["detailed_results"]["clarity"] = actionability
        results["scores"]["clarity"] = actionability.get("actionability_score", 0.0) * 5.0
    
    # ========== ATS ALIGNMENT EVALUATION ==========
    if "ats_alignment" in test_case["evaluation_criteria"]:
        criteria = test_case["evaluation_criteria"]["ats_alignment"]
        semantic_check = check_semantic_gaps(
            keywords_in_resume=model_outputs.get("ats_result", {}).get("matched_keywords", []),
            keywords_in_jd=model_outputs.get("ats_result", {}).get("top_jd_keywords", []),
            semantic_mappings=criteria.get("shallow_misses", [])
        )
        results["detailed_results"]["ats_alignment"] = semantic_check
        score = 5.0 if semantic_check["semantic_awareness"] == "YES" else 3.0
        results["scores"]["ats_alignment"] = score
    
    # ========== OVERALL SCORE ==========
    scores = results["scores"]
    if scores:
        overall = sum(scores.values()) / len(scores)
        results["overall_score"] = round(overall, 2)
    
    return results


# ============================================================================
# REPORTING
# ============================================================================

def print_evaluation_report(evaluation_result: Dict[str, Any]) -> None:
    """Pretty print evaluation results."""
    
    print("\n" + "="*80)
    print(f"TEST: {evaluation_result['test_id']} - {evaluation_result['test_name']}")
    print("="*80)
    
    print("\n📊 SCORES:")
    for criterion, score in evaluation_result.get("scores", {}).items():
        bar = "█" * int(score) + "░" * (5 - int(score))
        print(f"  {criterion:20s}: {score:.1f}/5.0  [{bar}]")
    
    if "overall_score" in evaluation_result:
        print(f"\n🎯 OVERALL: {evaluation_result['overall_score']}/5.0")
    
    print("\n📋 DETAILED RESULTS:")
    for criterion, details in evaluation_result.get("detailed_results", {}).items():
        print(f"\n  {criterion.upper()}:")
        if isinstance(details, dict):
            for key, value in details.items():
                if isinstance(value, list) and value:
                    print(f"    {key}:")
                    for item in value:
                        print(f"      - {item}")
                else:
                    print(f"    {key}: {value}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Simulate model output for TEST_001
    mock_outputs = {
        "tailored_resume": """
        John Doe
        john@example.com | 555-1234
        
        EXPERIENCE
        Senior Software Engineer | TechCorp | 2020-2023
        - Led migration of legacy monolith to microservices, achieving 40% performance gains
        - Optimized database performance with PostgreSQL tuning
        - Mentored 5+ junior developers and led technical initiatives
        - AWS migration experience
        """,
        "feedback": {
            "strengths": ["Microservices experience", "Database optimization"],
            "weaknesses": ["No mention of specific performance metrics", "Team size not quantified"],
            "priority_fixes": ["Quantify performance improvements", "Specify team size"]
        },
        "ats_result": {
            "matched_keywords": ["microservices", "database", "performance"],
            "top_jd_keywords": ["microservices", "performance", "postgresql"]
        }
    }
    
    result = run_evaluation(TEST_CASES[0], mock_outputs)
    print_evaluation_report(result)

