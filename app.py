import os
import openai
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# ✅ Load API Key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("🚨 ERROR: OPENAI_API_KEY is missing! Set it in .env file.")

app = Flask(__name__, template_folder="templates")
app.secret_key = "supersecretkey"
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

# 📌 AI Chatbot Route
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
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
