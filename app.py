import os
import openai
import requests
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, template_folder="templates")
app.secret_key = "supersecretkey"
CORS(app)

# Configure SQLite Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat_memory.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define Chat Memory Model
class ChatMemory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

# 📌 Function to filter restricted words before sending to OpenAI
def is_safe_prompt(prompt):
    blocked_words = ["violence", "explicit", "illegal", "weapon", "hate", "harm", "abuse", "scam", "adult", "kill", "terror"]
    for word in blocked_words:
        if word in prompt.lower():
            return False
    return True

# 📌 AI Chatbot Route (With Corrected OpenAI API Format)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    user_id = "default_user"

    # 🚨 Block restricted content BEFORE sending to OpenAI
    if not is_safe_prompt(user_message):
        return jsonify({"reply": "🚫 Sorry, I cannot process that request due to content restrictions."})

    try:
        # OpenAI API call with corrected function
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )

        ai_reply = response.choices[0].message.content

        return jsonify({"reply": ai_reply})

    except openai.OpenAIError as e:
        return jsonify({"reply": f"🚫 OpenAI API Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
