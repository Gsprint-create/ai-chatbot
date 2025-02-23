import os
import openai
import requests
from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Load API Keys
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
serpapi_key = os.getenv("SERPAPI_KEY")  # Google Image Search API Key

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
    user_id = db.Column(db.String(255), nullable=False)  # Unique user ID
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

# 📌 Detect if the user is asking for an image
def is_image_request(message):
    trigger_words = ["draw", "generate an image", "create an image", "show me a picture", "illustrate", "image of"]
    return any(word in message.lower() for word in trigger_words)

# 📌 Google Image Search (If AI fails)
def google_image_search(query):
    params = {
        "q": query,
        "tbm": "isch",
        "api_key": serpapi_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    if "images_results" in results:
        return results["images_results"][0]["original"]  # Return first image URL
    return None

# 📌 AI Chatbot Route (With Image Generation & Google Search)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")

    user_id = "default_user"

    try:
        # If user asks for an image, generate one with DALL·E
        if is_image_request(user_message):
            try:
                response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=user_message,
                    n=1,
                    size="1024x1024"
                )
                image_url = response.data[0].url
            except Exception:
                image_url = google_image_search(user_message)  # Use Google Search if AI fails

            if image_url:
                ai_reply = f"Here is the image you requested: {image_url} \n\n [Download Image](/download?url={image_url})"
            else:
                ai_reply = "🚫 I couldn't generate or find an image for that request."

        else:
            # Generate normal text response with ChatGPT
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful AI assistant."}, {"role": "user", "content": user_message}]
            )
            ai_reply = response.choices[0].message.content

        return jsonify({"reply": ai_reply})

    except openai.OpenAIError:
        return jsonify({"reply": "🚫 OpenAI rejected this request due to content policy restrictions."})

# 📌 Image Download Route
@app.route("/download")
def download_image():
    image_url = request.args.get("url")
    response = requests.get(image_url, stream=True)
    file_path = "static/downloaded_image.jpg"
    
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
    
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
