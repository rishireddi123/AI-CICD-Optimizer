# ai_analyzer.py

from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ──────────────────────────────────────────
# 1. MAIN ANALYSIS FUNCTION
# ──────────────────────────────────────────

def analyze_failure(log_text: str) -> dict:
    print("Sending log to Groq AI for analysis...")

    prompt = f"""You are a senior DevOps engineer analyzing a CI/CD pipeline failure.

FAILURE LOG:
{log_text}

Analyze this log carefully and return ONLY a valid JSON object.
No explanation. No markdown. Just the raw JSON.

Required format:
{{
  "root_cause": "One clear sentence explaining WHY this failed",
  "failed_step": "Which step failed — build, test, or deploy",
  "fix_suggestion": "Specific actionable fix the developer should apply",
  "is_flaky": false,
  "severity": "low or medium or high",
  "confidence": 0.85
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()
    print(f"Groq AI response received.")
    return json.loads(raw)


# ──────────────────────────────────────────
# 2. SAFE WRAPPER — handles errors
# ──────────────────────────────────────────

def safe_analyze(log_text: str) -> dict:
    try:
        return analyze_failure(log_text)
    except json.JSONDecodeError:
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": f"Analyze this CI log and return only JSON no markdown: {log_text}"}],
                max_tokens=600,
                temperature=0.1
            )
            raw = response.choices[0].message.content
            clean = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(clean)
        except:
            return {
                "root_cause": "Analysis failed — check logs manually",
                "failed_step": "unknown",
                "fix_suggestion": "Review the raw log in GitHub Actions",
                "is_flaky": False,
                "severity": "unknown",
                "confidence": 0.0
            }
    except Exception as e:
        print(f"AI analysis error: {e}")
        return {
            "root_cause": "Analysis failed — check logs manually",
            "failed_step": "unknown",
            "fix_suggestion": "Review the raw log in GitHub Actions",
            "is_flaky": False,
            "severity": "unknown",
            "confidence": 0.0
        }


# ──────────────────────────────────────────
# 3. TEST FUNCTION — run manually to verify
# ──────────────────────────────────────────

def test_analyzer():
    sample_log = """
    FAILED tests/test_calculator.py::test_divide
    AssertionError: assert 12 == 15
    where 12 = add(10, 2)
    short test summary info
    FAILED tests/test_calculator.py::test_divide - AssertionError: assert 12 == 15
    1 failed, 3 passed in 0.12s
    """

    print("Testing Groq AI analyzer with sample log...")
    result = safe_analyze(sample_log)

    print("\n========= AI DIAGNOSIS =========")
    print(f"Root cause:    {result['root_cause']}")
    print(f"Failed step:   {result['failed_step']}")
    print(f"Fix:           {result['fix_suggestion']}")
    print(f"Severity:      {result['severity']}")
    print(f"Confidence:    {result['confidence']}")
    print(f"Is flaky:      {result['is_flaky']}")
    print("================================\n")

if __name__ == "__main__":
    test_analyzer()