import os
import openai
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Load API Key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("🚨 ERROR: OPENAI_API_KEY is missing! Set it in .env file or Render Environment Variables.")

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

# 📌 Detect if user wants an image
def is_image_request(message):
    keywords = ["generate an image", "show me a picture", "draw", "illustrate", "image of"]
    return any(keyword in message.lower() for keyword in keywords)

# 📌 AI Chatbot Route with Image Generation
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    try:
        # If user asks for an image, use OpenAI's DALL·E API
        if is_image_request(user_message):
            response = openai.Image.create(
                model="dall-e-3",
                prompt=user_message,
                n=1,
                size="1024x1024",
                api_key=openai_api_key
            )
            image_url = response["data"][0]["url"]
            return jsonify({"reply": f"Here is the image you requested: {image_url}"})

        # Otherwise, use ChatGPT for normal text responses
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}],
            api_key=openai_api_key
        )
        ai_reply = response["choices"][0]["message"]["content"]
        return jsonify({"reply": ai_reply})

    except openai.error.OpenAIError as e:
        return jsonify({"reply": f"🚫 OpenAI Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
