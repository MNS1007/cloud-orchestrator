import subprocess
from google.adk.tools.function_tool import FunctionTool

@FunctionTool
def create_topic(project_id: str, topic_id: str) -> dict:
    """Create a Pub/Sub topic."""
    try:
        subprocess.run([
            "gcloud", "pubsub", "topics", "create", topic_id,
            "--project", project_id
        ], check=True)
        return {
            "message": f"✅ Topic '{topic_id}' created in project '{project_id}'."
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to create topic '{topic_id}':\n{e}"
        }

@FunctionTool
def create_subscription(project_id: str, topic_id: str, subscription_id: str) -> dict:
    """Create a Pub/Sub subscription."""
    try:
        subprocess.run([
            "gcloud", "pubsub", "subscriptions", "create", subscription_id,
            "--topic", topic_id,
            "--project", project_id
        ], check=True)
        return {
            "message": f"✅ Subscription '{subscription_id}' created for topic '{topic_id}'."
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to create subscription '{subscription_id}':\n{e}"
        }

@FunctionTool
def publish(project_id: str, topic_id: str, message: str) -> dict:
    """Publish a message to a Pub/Sub topic."""
    try:
        subprocess.run([
            "gcloud", "pubsub", "topics", "publish", topic_id,
            "--message", message,
            "--project", project_id
        ], check=True)
        return {
            "message": f"✅ Message published to topic '{topic_id}'."
        }
    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to publish message to topic '{topic_id}':\n{e}"
        }

@FunctionTool
def pull(project_id: str, subscription_id: str, max_messages: int = 10) -> dict:
    """
    Pull messages from a Pub/Sub subscription.

    Parameters:
    - project_id: GCP project ID
    - subscription_id: ID of the Pub/Sub subscription
    - max_messages: Number of messages to pull (default is 10)
    """
    try:
        result = subprocess.run(
            [
                "gcloud", "pubsub", "subscriptions", "pull", subscription_id,
                f"--limit={max_messages}",
                "--auto-ack",
                "--project", project_id
            ],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout.strip() or result.stderr.strip()

        if "No messages available" in output:
            return {
                "message": f"ℹ️ No messages available in subscription '{subscription_id}'."
            }

        return {
            "messages": output
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": f"❌ Failed to pull messages from subscription '{subscription_id}':\n{e.stderr.strip()}"
        }