import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import google.generativeai as genai
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', '*').split(',')]
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

@lru_cache(maxsize=1)
def get_classifier():
    return pipeline('sentiment-analysis')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini = genai.GenerativeModel("models/gemini-1.5-pro")
else:
    gemini = None
    logger.warning("GEMINI_API_KEY not set – AI guidance will use offline fallback")

# ── Emergency keyword classifier ─────────────────────────────────────────────
EMERGENCY_KEYWORDS = {
    'Medical':        ['heart','chest pain','bleeding','unconscious','seizure','stroke','broken','fracture','breathing','diabetic','overdose','poisoning','injury','medical','sick','hurt','pain','burn','wound','blood','pulse','ambulance','collapse','faint'],
    'Fire':           ['fire','flame','smoke','burning','explosion','blaze','ignite','gas leak','arson'],
    'Crime':          ['robbery','theft','stolen','murder','assault','attack','shooting','stabbing','kidnap','rape','harassment','crime','police','suspect','weapon','gang','threat','violence'],
    'Accident':       ['accident','crash','collision','car','vehicle','bike','truck','motorcycle','road','highway','hit','run over','pedestrian','drunk driving'],
    'Disaster':       ['earthquake','flood','tsunami','cyclone','tornado','hurricane','landslide','disaster','avalanche','drought','storm','lightning','volcanic'],
    'Women Safety':   ['women','girl','female','molestation','eve teasing','domestic violence','sexual','abused','stalking','dowry'],
    'Child Emergency':['child','baby','infant','toddler','missing child','abduction','childline','kidnapped child'],
}

def classify_by_keywords(text: str) -> tuple[str, float]:
    lower = text.lower()
    scores = {}
    for category, keywords in EMERGENCY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[category] = score
    if scores:
        best = max(scores, key=scores.get)
        confidence = min(0.95, 0.6 + scores[best] * 0.07)
        return best, confidence
    return None, 0.0

def detect_severity(text: str, confidence: float) -> str:
    lower = text.lower()
    critical_words = ['dying','unconscious','not breathing','massive bleeding','cardiac arrest','critical','severe']
    high_words = ['urgent','emergency','help','immediately','serious','bad']
    if any(w in lower for w in critical_words) or confidence > 0.90:
        return 'Critical'
    if any(w in lower for w in high_words) or confidence > 0.75:
        return 'High'
    if confidence > 0.55:
        return 'Medium'
    return 'Low'

# ── Gemini guidance ──────────────────────────────────────────────────────────
def get_emergency_guidance(user_text: str, emergency_type: str) -> str:
    if not gemini:
        return get_offline_guidance(emergency_type)
    prompt = f"""You are a calm, professional emergency response assistant.
A user is reporting a {emergency_type} emergency: "{user_text}"

Provide exactly 4 clear, numbered first-response steps they must take RIGHT NOW before help arrives.
Rules:
- Be direct and actionable
- Use simple language (assume panic)
- Each step on its own line starting with a number and period
- End with: "Call 112 immediately if you have not already"
- Keep each step under 20 words"""
    try:
        response = gemini.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return get_offline_guidance(emergency_type)

OFFLINE_GUIDANCE = {
    'Medical': '1. Keep the person calm and still.\n2. Check for breathing — perform CPR if unresponsive.\n3. Apply firm pressure to any bleeding wound.\n4. Call 112 immediately if you have not already.',
    'Fire': '1. Evacuate everyone immediately — leave belongings.\n2. Stay low to avoid smoke inhalation.\n3. Close doors to slow fire spread.\n4. Call 112 immediately if you have not already.',
    'Crime': '1. Move to a safe, crowded location immediately.\n2. Do not confront the suspect.\n3. Note descriptions of people and vehicles.\n4. Call 112 immediately if you have not already.',
    'Accident': '1. Do not move injured persons unless in immediate danger.\n2. Turn off vehicle ignition to prevent fire.\n3. Apply pressure to wounds with clean cloth.\n4. Call 112 immediately if you have not already.',
    'Disaster': '1. Move to higher ground or designated shelter.\n2. Avoid downed power lines and flooded roads.\n3. Follow official evacuation instructions.\n4. Call 112 immediately if you have not already.',
    'Women Safety': '1. Move to a crowded, well-lit public area.\n2. Call Womens Helpline: 1091.\n3. Share live location with a trusted contact.\n4. Call 112 immediately if you have not already.',
    'Child Emergency': '1. Stay with the child and keep them calm.\n2. Do not leave the child unattended.\n3. Call Childline: 1098.\n4. Call 112 immediately if you have not already.',
}

def get_offline_guidance(emergency_type: str) -> str:
    return OFFLINE_GUIDANCE.get(emergency_type, OFFLINE_GUIDANCE['Medical'])

# ── API Routes ────────────────────────────────────────────────────────────────
@app.route('/api/classify', methods=['POST'])
def classify():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    text = (data.get('text') or '').strip()
    location = data.get('location')

    if not text:
        return jsonify({'error': 'Empty input'}), 400
    if len(text) > 2000:
        return jsonify({'error': 'Input too long'}), 400

    # 1. Keyword-based classification (fast, offline-friendly)
    kw_type, kw_confidence = classify_by_keywords(text)

    # 2. Sentiment-based classification as fallback
    try:
        classifier = get_classifier()
        sentiment = classifier(text[:512])[0]
        sent_confidence = sentiment['score']
        sent_type = 'Medical' if sentiment['label'] == 'NEGATIVE' else 'General Distress'
    except Exception as e:
        logger.error(f"Classifier error: {e}")
        sent_confidence = 0.6
        sent_type = 'Medical'

    # 3. Pick best classification — keyword wins when found
    if kw_type:
        emergency_type = kw_type
        confidence = kw_confidence
    else:
        emergency_type = sent_type
        confidence = sent_confidence

    # 4. Severity detection
    severity = detect_severity(text, confidence)

    # 5. AI guidance
    guidance = get_emergency_guidance(text, emergency_type)

    # 6. Location
    lat = location.get('lat') if location else None
    lon = location.get('lon') if location else None

    logger.info(f"Emergency: {emergency_type} | Severity: {severity} | Confidence: {round(confidence*100,1)}% | Location: {bool(lat)}")

    return jsonify({
        'emergencyType': emergency_type,
        'confidence': round(confidence * 100, 1),
        'severity': severity,
        'locationReceived': bool(lat and lon),
        'guidance': guidance,
        'coordinates': {'lat': lat, 'lon': lon} if lat and lon else None,
    })

@app.route('/api/sos', methods=['POST'])
def sos_event():
    data = request.get_json(silent=True) or {}
    location = data.get('location')
    profile = data.get('profile', {})
    logger.info(f"SOS Triggered | Location: {location} | Blood: {profile.get('bloodGroup', 'Unknown')}")
    return jsonify({'status': 'received', 'message': 'SOS event logged. Emergency services should be called via 112.'})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'gemini': bool(gemini), 'version': '2.0'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', host='0.0.0.0', port=port)
