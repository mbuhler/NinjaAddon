import os
import requests
from dotenv import load_dotenv

load_dotenv()

def notify_discord(message: str):
    """Sends a message to a Discord channel using a webhook."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("Warning: Discord webhook URL not set. Cannot send notification.")
        return

    data = {
        "username": "StrategyMonitorBot",
        "content": message
    }

    try:
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Discord notification: {e}")

def notify_email(subject: str, body: str):
    """Sends an email notification."""
    # This is a placeholder for the email notification logic.
    print(f"Sending email: {subject} - {body}")

def notify_slack(message: str):
    """Sends a message to a Slack channel using a webhook."""
    # This is a placeholder for the Slack notification logic.
    print(f"Sending Slack message: {message}")

def trigger_alert(strategy_name: str, message: str):
    """Triggers an alert to the configured notification channels."""

    full_message = f"**{strategy_name} Alert**\n{message}\nReview at: http://localhost:8000/strategy/{strategy_name}"

    if os.getenv("DISCORD_WEBHOOK_URL"):
        notify_discord(full_message)

    # Add calls to other notification handlers here
    # notify_email("Strategy Alert", full_message)
    # notify_slack(full_message)
