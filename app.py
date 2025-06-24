from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import google.generativeai as genai

genai.configure(api_key="AIzaSyBr2K0aqQnrC2XVuiL5L-gzFPyTNAZCgmQ")
for model in genai.list_models():
    print(model.name)


app = Flask(__name__)
CORS(app)

# Load classifier
classifier = pipeline('sentiment-analysis')

# ✅ Configure Gemini with Google Cloud API key
genai.configure(api_key="AIzaSyBr2K0aqQnrC2XVuiL5L-gzFPyTNAZCgmQ")

# Use Gemini 1.5 Pro
gemini = genai.GenerativeModel("models/gemini-1.5-pro")

def get_emergency_guidance(user_text):
    prompt = f"""
You are a helpful emergency assistant. A user said: "{user_text}"

Give 3 clear steps they should follow right now, before professional help arrives.
Use bullet points. Be calm, helpful, and easy to understand.
"""
    try:
        response = gemini.generate_content([prompt])
        return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)
        return "⚠️ Emergency guidance is temporarily unavailable."

@app.route('/api/classify', methods=['POST'])
def classify():
    data = request.get_json()
    text = data.get('text', '')
    location = data.get('location')

    if not text.strip():
        return jsonify({'error': 'Empty input'}), 400

    # Classify
    result = classifier(text)[0]
    emergency = "Medical" if 'NEGATIVE' in result['label'] else "General Distress"
    score = result['score']

    # AI guidance
    guidance = get_emergency_guidance(text)

    # Location (optional)
    lat = location.get('lat') if location else None
    lon = location.get('lon') if location else None

    return jsonify({
        'emergencyType': emergency,
        'confidence': round(score * 100, 2),
        'locationReceived': bool(lat and lon),
        'guidance': guidance
    })

if __name__ == '__main__':
    app.run(debug=True)
