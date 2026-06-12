# slack_notifier.py

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
from dotenv import load_dotenv

load_dotenv()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# ──────────────────────────────────────────
# 1. SEND FAILURE ALERT TO SLACK
# ──────────────────────────────────────────

def send_failure_alert(analysis: dict, run_id: str, repo: str):
    print("Sending failure alert to Slack...")

    # Color based on severity
    color = {
        "high":    "#E24B4A",   # red
        "medium":  "#EF9F27",   # orange
        "low":     "#639922",   # green
        "unknown": "#888780"    # gray
    }.get(analysis.get("severity", "unknown"), "#888780")

    try:
        client.chat_postMessage(
            channel="#devops-alerts",
            text=f"Pipeline failure detected in {repo}",
            attachments=[
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🚨 Pipeline Failure Detected"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Repository:*\n`{repo}`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Severity:*\n`{analysis.get('severity', 'unknown').upper()}`"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Root Cause:*\n{analysis.get('root_cause', 'Unknown')}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Suggested Fix:*\n{analysis.get('fix_suggestion', 'Review the logs')}"
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Run ID: `{run_id}` · Confidence: `{int(analysis.get('confidence', 0) * 100)}%` · Powered by Groq AI"
                                }
                            ]
                        }
                    ]
                }
            ]
        )
        print("Slack alert sent successfully!")

    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")


# ──────────────────────────────────────────
# 2. SEND FLAKY TEST ALERT TO SLACK
# ──────────────────────────────────────────

def send_flaky_alert(flaky: dict, repo: str):
    print("Sending flaky test alert to Slack...")

    try:
        client.chat_postMessage(
            channel="#devops-alerts",
            text=f"Flaky test detected in {repo}",
            attachments=[
                {
                    "color": "#EF9F27",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "⚠️ Flaky Test Detected"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Repository:*\n`{repo}`"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Failure Rate:*\n`{flaky.get('failure_rate', 'N/A')}`"
                                }
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Likely Cause:*\n{flaky.get('likely_cause', 'Unknown')}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Recommendation:*\n{flaky.get('recommendation', 'Investigate the test')}"
                            }
                        }
                    ]
                }
            ]
        )
        print("Flaky test alert sent successfully!")

    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")


# ──────────────────────────────────────────
# 3. SEND DEPLOY SUMMARY TO SLACK
# ──────────────────────────────────────────

def send_deploy_summary(summary: str, repo: str):
    print("Sending deploy summary to Slack...")

    try:
        client.chat_postMessage(
            channel="#devops-alerts",
            text=f"Deploy summary for {repo}",
            attachments=[
                {
                    "color": "#4A90D9",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Pipeline Health Summary"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Repository:* `{repo}`\n\n{summary}"
                            }
                        }
                    ]
                }
            ]
        )
        print("Deploy summary sent successfully!")

    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")


# ──────────────────────────────────────────
# 4. TEST FUNCTION
# ──────────────────────────────────────────

if __name__ == "__main__":
    print("Testing Slack notifications...")

    # Test failure alert
    test_analysis = {
        "root_cause": "The test_divide function is calling add instead of divide",
        "failed_step": "test",
        "fix_suggestion": "Update test_divide to call the correct divide function",
        "severity": "low",
        "confidence": 0.95,
        "is_flaky": False
    }

    send_failure_alert(test_analysis, "test-run-123", "rishireddi123/AI-CICD-Optimizer")

    # Test flaky alert
    test_flaky = {
        "is_flaky": True,
        "likely_cause": "Test fails intermittently due to inconsistent expected values",
        "recommendation": "Quarantine the test and investigate the root cause",
        "failure_rate": "50%"
    }

    send_flaky_alert(test_flaky, "rishireddi123/AI-CICD-Optimizer")

    # Test deploy summary
    send_deploy_summary(
        "Pipeline health is concerning with a 50% failure rate over the last 10 runs.",
        "rishireddi123/AI-CICD-Optimizer"
    )

    print("\nAll Slack notifications sent!")