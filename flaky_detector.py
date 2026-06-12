from groq import Groq
import sqlite3
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ──────────────────────────────────────────
# 1. QUERY RUN HISTORY FROM DATABASE
# ──────────────────────────────────────────

def get_run_history(repo: str) -> list:
    conn = sqlite3.connect("pipeline.db")
    rows = conn.execute("""
        SELECT run_id, status, log_text
        FROM runs
        WHERE repo = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (repo,)).fetchall()
    conn.close()
    return rows

# ──────────────────────────────────────────
# 2. DETECT FLAKY TEST PATTERN
# ──────────────────────────────────────────

def detect_flaky(repo: str) -> dict:
    print(f"Checking flaky test pattern for {repo}...")

    history = get_run_history(repo)

    if not history:
        return {"is_flaky": False, "reason": "No run history found"}

    total    = len(history)
    failures = [r for r in history if r[1] == "failure"]
    passes   = [r for r in history if r[1] == "success"]

    failure_rate = len(failures) / total
    print(f"Run history: {total} runs — {len(failures)} failures, {len(passes)} passes")
    print(f"Failure rate: {failure_rate:.0%}")

    # If always passes or always fails — not flaky
    if failure_rate == 0:
        return {
            "is_flaky": False,
            "reason": "All runs passed — no flaky pattern detected",
            "failure_rate": "0%"
        }

    if failure_rate == 1.0:
        return {
            "is_flaky": False,
            "reason": "All runs failed — this is a real bug not a flaky test",
            "failure_rate": "100%"
        }

    # Intermittent failures — ask the AI
    sample_log = failures[0][2] if failures else ""
    history_summary = f"{len(failures)} out of {total} recent runs failed intermittently."

    prompt = f"""You are a senior DevOps engineer analyzing test stability.

This test has the following pattern:
- {history_summary}
- Failure rate: {failure_rate:.0%}
- Sample failure log: {sample_log[:500]}

Based on this intermittent failure pattern, analyze if this is a flaky test.
Return ONLY a valid JSON object. No explanation. No markdown.

Required format:
{{
    "is_flaky": true,
    "likely_cause": "One sentence explaining why this test is flaky",
    "recommendation": "Specific action to fix or quarantine this flaky test",
    "failure_rate": "{failure_rate:.0%}"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)

    return result

# ──────────────────────────────────────────
# 3. DEPLOY SUMMARY GENERATOR
# ──────────────────────────────────────────

def generate_deploy_summary(repo: str) -> str:
    print(f"\nGenerating deploy summary for {repo}...")

    history = get_run_history(repo)

    if not history:
        return "No run history available."

    total    = len(history)
    failures = len([r for r in history if r[1] == "failure"])
    passes   = total - failures

    prompt = f"""You are a DevOps engineer writing a short deploy summary.

Recent pipeline activity for {repo}:
- Total runs analyzed: {total}
- Successful runs: {passes}
- Failed runs: {failures}
- Failure rate: {failures/total:.0%}

Write a 2-3 sentence plain English summary of the pipeline health.
Be concise and professional. Start with the overall status.
Example: 'Pipeline health is moderate with a 50% failure rate over the last 10 runs...'"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.1
    )

    return response.choices[0].message.content.strip()

# ──────────────────────────────────────────
# 4. TEST BOTH FEATURES
# ──────────────────────────────────────────

if __name__ == "__main__":
    repo = "rishireddi123/AI-CICD-Optimizer"

    print("=" * 50)
    print("FLAKY TEST DETECTOR")
    print("=" * 50)
    result = detect_flaky(repo)
    print(f"\nIs flaky:      {result.get('is_flaky')}")
    print(f"Likely cause:  {result.get('likely_cause') or result.get('reason')}")
    print(f"Recommend:     {result.get('recommendation', 'N/A')}")
    print(f"Failure rate:  {result.get('failure_rate', 'N/A')}")

    print("\n" + "=" * 50)
    print("DEPLOY SUMMARY")
    print("=" * 50)
    summary = generate_deploy_summary(repo)
    print(f"\n{summary}")
    print("=" * 50)