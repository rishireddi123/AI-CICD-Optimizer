from fastapi import FastAPI, Request
from dotenv import load_dotenv
from ai_analyzer import safe_analyze
from flaky_detector import detect_flaky, generate_deploy_summary
import sqlite3
import requests
import zipfile
import io
import re
import os

load_dotenv()

app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO")

# ──────────────────────────────────────────
# 1. DATABASE SETUP
# ──────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("pipeline.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id    TEXT,
            repo      TEXT,
            status    TEXT,
            log_text  TEXT,
            root_cause TEXT,
            fix_suggestion TEXT,
            severity  TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")

def save_to_db(run_id, repo, log_text, analysis):
    conn = sqlite3.connect("pipeline.db")
    conn.execute(
        """INSERT INTO runs 
        (run_id, repo, status, log_text, root_cause, fix_suggestion, severity) 
        VALUES (?,?,?,?,?,?,?)""",
        (
            str(run_id),
            repo,
            "failure",
            log_text,
            analysis["root_cause"],
            analysis["fix_suggestion"],
            analysis["severity"]
        )
    )
    conn.commit()
    conn.close()
    print(f"Saved run {run_id} with AI analysis to database.")

# ──────────────────────────────────────────
# 2. FETCH LOG FROM GITHUB
# ──────────────────────────────────────────

def fetch_log(run_id, repo):
    print(f"Fetching log for run {run_id}...")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/logs"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"Failed to fetch log: {resp.status_code} {resp.text}")
        return "Log unavailable."

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    full_log = ""
    for name in z.namelist():
        full_log += z.read(name).decode("utf-8", errors="ignore")

    clean = re.sub(r'\x1b\[[0-9;]*m', '', full_log)
    clean = re.sub(r'^\d{4}-\d{2}-\d{2}T[\d:.]+Z ', '', clean, flags=re.M)

    print(f"Log fetched. Length: {len(clean)} characters.")
    return clean[-4000:]

# ──────────────────────────────────────────
# 3. WEBHOOK ENDPOINT
# ──────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    print("Server started and ready to receive webhooks.")

@app.get("/")
def root():
    return {"status": "AI CI/CD Optimizer is running"}

@app.post("/webhook")
async def github_webhook(request: Request):
    event   = request.headers.get("X-GitHub-Event", "unknown")
    payload = await request.json()

    print(f"\nReceived event: {event}")

    if event != "workflow_run":
        return {"status": "ignored", "reason": "not a workflow_run event"}

    run        = payload.get("workflow_run", {})
    conclusion = run.get("conclusion")
    run_id     = run.get("id")
    repo       = payload.get("repository", {}).get("full_name")

    print(f"Run ID: {run_id} | Conclusion: {conclusion} | Repo: {repo}")

    if conclusion != "failure":
        return {"status": "ignored", "reason": f"conclusion was {conclusion}"}

    print("FAILURE DETECTED — starting full analysis pipeline...")

    # Step 1 — Fetch the log
    log_text = fetch_log(run_id, repo)

    # Step 2 — Analyze with AI
    print("Sending log to AI...")
    analysis = safe_analyze(log_text)

    # Step 3 — Print the diagnosis
    print("\n========= AI DIAGNOSIS =========")
    print(f"Root cause:  {analysis['root_cause']}")
    print(f"Failed step: {analysis['failed_step']}")
    print(f"Fix:         {analysis['fix_suggestion']}")
    print(f"Severity:    {analysis['severity']}")
    print(f"Confidence:  {analysis['confidence']}")
    print("================================\n")

    # Step 4 — Save everything to DB
    save_to_db(run_id, repo, log_text, analysis)

    # Step 5 — Check for flaky tests
    print("\nChecking for flaky test pattern...")
    flaky = detect_flaky(repo)
    if flaky.get("is_flaky"):
        print(f"⚠️  FLAKY TEST DETECTED!")
        print(f"Likely cause:  {flaky.get('likely_cause')}")
        print(f"Recommendation: {flaky.get('recommendation')}")
    else:
        print(f"No flaky pattern detected.")

    # Step 6 — Generate deploy summary
    summary = generate_deploy_summary(repo)
    print(f"\n📊 DEPLOY SUMMARY:")
    print(f"{summary}")

    print("\nDone. Slack notification coming in Day 5.")
    return {"status": "received", "run_id": run_id, "analysis": analysis}