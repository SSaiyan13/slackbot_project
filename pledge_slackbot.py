import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify

# Get Slack Bot Token from environment variable
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    raise ValueError("Missing Slack Bot Token! Set SLACK_BOT_TOKEN as an environment variable.")

client = WebClient(token=SLACK_BOT_TOKEN)

# Initialize Flask app
app = Flask(__name__)

# ✅ Route to handle Slack events (handles event verification & commands)
@app.route("/slack/events", methods=["POST"])
def handle_slack_event():
    data = request.get_json(force=True)  # 🔹 Ensure JSON is received properly

    # ✅ Handle Slack URL verification
    if "challenge" in data:
        return jsonify({"challenge": data["challenge"]})

    # ✅ Extract command text (for /review command)
    command_text = data.get("event", {}).get("text", "")
    
    if command_text:
        parts = command_text.split(" ", 2)
        if len(parts) < 3:
            return jsonify({"text": "Invalid format. Use `/review @username [positive|critical] comment`."})

        username, comment_type, comment = parts[0].strip("@"), parts[1].lower(), parts[2].strip()

        if comment_type not in ["positive", "critical"]:
            return jsonify({"text": "Invalid comment type. Use either 'positive' or 'critical'."})

        user_id = get_user_id_by_name(username)
        if not user_id:
            return jsonify({"text": f"User '{username}' not found."})

        send_direct_message(user_id, comment, comment_type)

        return jsonify({"text": f"Message sent to {username} with a {comment_type} comment!"})

    return jsonify({"text": "Please provide a username, comment type, and comment."})

# ✅ Fetch User ID from Slack
def get_user_id_by_name(username):
    try:
        response = client.users_list()
        for user in response["members"]:
            if user.get("name") == username:
                return user["id"]
        return None
    except SlackApiError as e:
        print(f"Error fetching user list: {e.response['error']}")
        return None

# ✅ Send Direct Message
def send_direct_message(user_id, comment, comment_type):
    try:
        message = f"You have a new {comment_type} review comment: {comment}"
        client.chat_postMessage(channel=user_id, text=message)
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

# ✅ Test Route to Check if Server is Running
@app.route("/", methods=["GET"])
def test_server():
    return jsonify({"text": "Slack bot is running on Render!"})

# ✅ Run Flask with Dynamic Port for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render uses dynamic ports above 10000
    app.run(host="0.0.0.0", port=port)
