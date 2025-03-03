import os
import logging
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Slack Bot Token
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)

# Health check route
@app.route("/", methods=["GET"])
def health_check():
    logging.debug("Health check requested.")
    return jsonify({"text": "Slack bot is running on Render!"})

# Slack event subscription endpoint
@app.route("/slack/events", methods=["POST"])
def handle_slack_event():
    data = request.get_json(force=True)
    logging.debug(f"Received data from Slack: {data}")

    # Handle Slack URL verification challenge
    if "challenge" in data:
        logging.debug("Handling Slack URL verification challenge.")
        return jsonify({"challenge": data["challenge"]})

    # Handle Slack slash command (/review)
    if "event" in data:
        event_data = data["event"]
        command_text = event_data.get("text", "")
        logging.debug(f"Command text received: {command_text}")

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

    logging.debug("Event received without a recognizable command.")
    return jsonify({"text": "Event received!"})

# Fetch User ID from Slack
def get_user_id_by_name(username):
    try:
        response = client.users_list()
        for user in response["members"]:
            if user.get("name") == username:
                return user["id"]
        logging.debug(f"User '{username}' not found.")
        return None
    except SlackApiError as e:
        logging.error(f"Error fetching user list: {e.response['error']}")
        return None

# Send Direct Message
def send_direct_message(user_id, comment, comment_type):
    try:
        message = f"You have a new {comment_type} review comment: {comment}"
        client.chat_postMessage(channel=user_id, text=message)
        logging.debug(f"Sent message to user ID {user_id}.")
    except SlackApiError as e:
        logging.error(f"Error sending message: {e.response['error']}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
    
