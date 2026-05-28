# ResQ.AI Backend

Flask REST API powering the ResQ.AI emergency assistant. Provides emergency classification, Gemini AI guidance generation, and SOS event logging.

[![Tests](https://img.shields.io/badge/Tests-41%2F41_passing-brightgreen)](#test-coverage)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com)
[![Render](https://img.shields.io/badge/Deployed_on-Render.com-46E3B7?logo=render)](https://render.com)

Live URL: https://resqai-backend.onrender.com

---

## Requirements

- Python 3.11
- pip 23+

```bash
pip install -r requirements.txt
```

## Environment Setup

```bash
cp .env.example .env
# Edit .env and add your values
```

`.env` variables:

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Google Gemini API key (get free at aistudio.google.com) |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins (default: `*`) |
| `FLASK_DEBUG` | No | Set `true` for debug mode (never in production) |
| `FLASK_ENV` | No | `production` or `development` |
| `PORT` | No | Auto-set by Render/Heroku — leave blank for local |

```env
GEMINI_API_KEY=AIza...your_key_here
ALLOWED_ORIGINS=https://resqai-frontend.vercel.app,http://localhost:3000
FLASK_DEBUG=false
FLASK_ENV=production
```

---

## Run Locally

```bash
python app.py
# Server starts at http://localhost:5000
```

Test health: `curl http://localhost:5000/api/health`

## Run Tests

```bash
python test_app.py
```

Expected output:
```
============================================================
  RESULTS: 41/41 tests passed
============================================================
Ran 41 tests in 0.022s  OK
```

No PyTorch or model downloads needed — all heavy dependencies are mocked.

---

## Deploy to Render.com

1. Push this repo to GitHub
2. Go to https://render.com ? New ? Web Service
3. Connect your GitHub repo
4. Settings are auto-loaded from `render.yaml`. Verify:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Runtime**: Python 3
5. Add environment variables in the Render dashboard:
   - `GEMINI_API_KEY` = your key
   - `ALLOWED_ORIGINS` = `https://your-frontend.vercel.app,http://localhost:3000`
6. Deploy ? live at `https://resqai-backend.onrender.com`

---

## API Reference

Base URL: `https://resqai-backend.onrender.com`

### POST /api/classify

**Request**
```json
{
  "text": "Someone is having a heart attack",
  "location": { "lat": 28.6139, "lon": 77.2090 }
}
```

**Response `200 OK`**
```json
{
  "emergencyType": "Medical",
  "confidence": 88.0,
  "severity": "Critical",
  "locationReceived": true,
  "guidance": "1. Help them sit...\n2. ...\n3. ...\n4. Call 112 immediately.",
  "coordinates": { "lat": 28.6139, "lon": 77.209 }
}
```

| Field | Type | Values |
|---|---|---|
| `emergencyType` | string | Medical, Fire, Crime, Accident, Disaster, Women Safety, Child Emergency, General Distress |
| `severity` | string | Critical, High, Medium, Low |
| `confidence` | number | 0–100 (percentage) |
| `guidance` | string | 4-step numbered first-aid text |

**Errors**: `400` (empty/long/invalid input), `500` (server error)

---

### POST /api/sos

**Request**: `{ "location": {"lat":0,"lon":0}, "profile": {"bloodGroup":"O+"} }`  
**Response**: `{ "status": "received", "message": "SOS event logged..." }`

### GET /api/health

**Response**: `{ "status": "ok", "gemini": true, "version": "2.0" }`

---

## Classification Logic

```
User Text Input
    ¦
    +- Keyword Engine (fast, offline)
    ¦   70+ terms across 7 categories
    ¦   confidence = min(0.95, 0.6 + matches × 0.07)
    ¦   WINS when any match is found
    ¦
    +- HuggingFace distilbert sentiment (fallback only)
    ¦
    ?
Severity: Critical / High / Medium / Low
    ¦
    ?
Gemini 1.5 Pro ? 4-step first-aid guidance
    (offline pre-written fallback if no API key)
```

---

## File Structure

```
resqai-backend/
+-- app.py              ? All application code
+-- test_app.py         ? 41-test suite
+-- requirements.txt    ? Python dependencies
+-- Procfile            ? Gunicorn start command (Render/Heroku)
+-- render.yaml         ? Render service auto-configuration
+-- runtime.txt         ? Python version pin (python-3.11.0)
+-- .env.example        ? Environment variable template
+-- README.md
```

---

## Test Coverage (41/41)

| Class | Tests | Coverage |
|---|---|---|
| TestKeywordClassifier | 9 | All 7 emergency types, empty/unknown |
| TestSeverityDetection | 6 | All severity levels + confidence thresholds |
| TestOfflineGuidance | 2 | All types covered, 112 mentioned |
| TestAPIEndpoints | 18 | All routes, error codes, CORS, location, SOS |
| TestAPIResponseStructure | 4 | Field types, valid categories, non-empty guidance |
| **Total** | **41** | |

---

## Security

- API keys in `.env` only — never hardcoded, never committed
- `.gitignore` excludes `.env`, `venv/`, `__pycache__/`
- `ALLOWED_ORIGINS` restricts CORS to configured domains
- Input length capped at 2000 characters
- Input type validated on all endpoints

---

## See Also

Full project documentation, frontend code, architecture: [resqai-frontend README](https://github.com/Sajal-Srivastava/resqai-frontend)
