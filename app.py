import os
import openai
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask app
app = Flask(__name__, template_folder="templates")
CORS(app)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat_history.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define Chat History Model
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    bot_reply = db.Column(db.Text, nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

# Function to save chat messages to the database
def save_chat(user_message, bot_reply):
    new_chat = ChatMessage(user_message=user_message, bot_reply=bot_reply)
    db.session.add(new_chat)
    db.session.commit()

# Retrieve chat history (latest 10 messages)
@app.route("/history", methods=["GET"])
def get_history():
    chat_history = ChatMessage.query.order_by(ChatMessage.id.desc()).limit(10).all()
    history = [{"user": chat.user_message, "bot": chat.bot_reply} for chat in chat_history]
    return jsonify(history)

# AI Chatbot Route
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
        # Generate AI Response
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        ai_reply = response["choices"][0]["message"]["content"]

        # Save chat history
        save_chat(user_message, ai_reply)

        return jsonify({"reply": ai_reply})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
