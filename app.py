# ==========================
# 🚀 BACKEND (app.py)
# ==========================
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline

app = Flask(__name__)
CORS(app)

classifier = pipeline('sentiment-analysis')

@app.route('/api/classify', methods=['POST'])
def classify():
    data = request.get_json()
    text = data.get('text', '')
    location = data.get('location')

    if not text.strip():
        return jsonify({'error': 'Empty input'}), 400

    result = classifier(text)[0]
    label = result['label']
    score = result['score']

    # Logic: NEGATIVE = Medical, POSITIVE = General Distress (for demo)
    if 'NEGATIVE' in label:
        emergency = "Medical"
    else:
        emergency = "General Distress"

    # ✅ Safe location extraction
    lat = location.get('lat') if location else None
    lon = location.get('lon') if location else None
    print(f"Location received: lat={lat}, lon={lon}")

    return jsonify({
        'emergencyType': emergency,
        'confidence': round(score * 100, 2),
        'locationReceived': bool(lat and lon)
    })

if __name__ == '__main__':
    app.run(debug=True)
