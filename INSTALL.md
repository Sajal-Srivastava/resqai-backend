# ResQ.AI — Installation Guide

> Complete setup guide to run the ResQ.AI platform locally on any machine.

---

## Prerequisites

Make sure these are installed before starting:

| Tool | Version | Download |
|------|---------|----------|
| Git | Any | https://git-scm.com/downloads |
| Node.js | 18+ | https://nodejs.org |
| Python | 3.11+ | https://www.python.org/downloads |

Verify your installs:

```bash
git --version
node --version
python --version
```

---

## Step 1 — Clone Both Repositories

```bash
# Clone the frontend
git clone https://github.com/Sajal-Srivastava/resqai-frontend.git

# Clone the backend
git clone https://github.com/Sajal-Srivastava/resqai-backend.git
```

---

## Step 2 — Set Up the Backend (Python / Flask)

```bash
# Navigate into the backend folder
cd resqai-backend

# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the example env file and fill in your keys
cp .env.example .env
```

Open `.env` and set your Gemini API key (free at https://aistudio.google.com/app/apikey):

```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
FLASK_DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000
```

Start the backend:

```bash
python app.py
```

Backend runs at: **http://localhost:5000**  
Health check: **http://localhost:5000/api/health**

---

## Step 3 — Set Up the Frontend (React)

Open a **new terminal** and:

```bash
# Navigate into the frontend folder
cd resqai-frontend

# Install dependencies
npm install

# The .env.development already points to localhost:5000 by default
# No changes needed for local development
```

Start the frontend:

```bash
npm start
```

Frontend opens at: **http://localhost:3000**

---

## Step 4 — Verify Everything Works

With both servers running, open **http://localhost:3000** in your browser.

Test the API directly:

```bash
# Health check
curl http://localhost:5000/api/health

# Test classification
curl -X POST http://localhost:5000/api/classify \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"heart attack chest pain\"}"
```

Expected classify response:
```json
{
  "emergencyType": "Medical",
  "severity": "High",
  "confidence": 81.0,
  "guidance": "..."
}
```

---

## Quick Reference — All Commands

```bash
# ── BACKEND ──────────────────────────────────────────────────
git clone https://github.com/Sajal-Srivastava/resqai-backend.git
cd resqai-backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt
cp .env.example .env           # then edit .env with your API key
python app.py

# ── FRONTEND ─────────────────────────────────────────────────
git clone https://github.com/Sajal-Srivastava/resqai-frontend.git
cd resqai-frontend
npm install
npm start
```

---

## Running Tests (Backend)

```bash
cd resqai-backend
python test_app.py
```

Expected: **41 tests pass**

---

## Environment Variables Reference

### Backend (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Optional | Google Gemini AI key — enables real AI guidance |
| `FLASK_ENV` | No | `development` or `production` |
| `FLASK_DEBUG` | No | `true` or `false` |
| `ALLOWED_ORIGINS` | No | CORS origins, comma-separated |
| `PORT` | No | Auto-set by cloud platforms |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `REACT_APP_BACKEND_URL` | `http://localhost:5000` | Points to the Flask backend |

---

## Troubleshooting

**`python` not found on Windows** — try `py` or `python3` instead:
```bash
py -m venv venv
py app.py
```

**Port 5000 already in use:**
```bash
# Windows — find and kill the process
netstat -ano | findstr :5000
taskkill /PID <pid> /F
```

**`npm install` fails** — clear cache and retry:
```bash
npm cache clean --force
npm install
```

**CORS errors in browser** — make sure `ALLOWED_ORIGINS` in your `.env` includes `http://localhost:3000`

---

## Live Production URLs

| Service | URL |
|---------|-----|
| Frontend | https://resqai-frontend.vercel.app |
| Backend API | https://resqai-backend-production.up.railway.app |
| Health Check | https://resqai-backend-production.up.railway.app/api/health |

---

## GitHub Repositories

- **Frontend**: https://github.com/Sajal-Srivastava/resqai-frontend
- **Backend**: https://github.com/Sajal-Srivastava/resqai-backend
