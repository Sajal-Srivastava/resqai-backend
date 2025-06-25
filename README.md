# 🧠 ResQ.AI – Backend (Flask + AI)

This is the backend service for **ResQ.AI**, an AI-powered emergency assistant that classifies emergency types based on user input (voice/text), and offers immediate, actionable guidance.

> 🔗 Pairs with frontend: [ResQ.AI Frontend Repo](https://github.com/Sajal-Srivastava/resqai-frontend)

---

## 💡 What It Does

- Accepts user input (`text`, optional `location`)
- Uses HuggingFace Transformers to classify the emergency
- Returns emergency type (e.g., Medical, Fire, Crime)
- Sends back confidence score + location status
- Can be extended to use Gemini / GPT for guidance
- Built with Flask + Transformers (Lightweight and fast)

---

## ⚙️ Tech Stack

| Layer        | Tech                        |
|--------------|-----------------------------|
| Web Server   | Flask (Python)              |
| AI Model     | HuggingFace Transformers    |
| Deployment   | Render.com / Any Python host|
| Integration  | REST API (CORS enabled)     |

---

## 📁 Project Structure

