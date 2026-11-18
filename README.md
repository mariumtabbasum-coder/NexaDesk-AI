# NexaDesk AI
**Knowledge that answers. AI that assists.**

NexaDesk AI is a modular knowledge assistant prototype combining FAQ retrieval, semantic search, chat sessions, and utility tools.

## Stack
Flask · Bootstrap 5 · Vanilla JavaScript · Gemini API · NumPy · JSON storage

## Setup
1. Create and activate a virtual environment.
2. Install: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`.
4. Add your Gemini API key. Weather is optional; add an OpenWeather API key to enable weather lookups.
5. Run: `python app.py`
6. Open `http://127.0.0.1:5000`

## Features
- FAQ CRUD, category filtering, JSON import/export
- Semantic retrieval with Gemini embeddings (local TF-IDF-like fallback when API unavailable)
- Top-three retrieval results and similarity score display
- Knowledge-grounded answers and unknown-question logging
- Chat history, new conversations, rename/delete
- Calculator, weather, currency conversion, age calculator tools
- Feedback controls, dashboard summary, responsive drawer navigation

## Notes
- Embedding fallback is a lightweight token-based vector, not a substitute for a production embedding model.
- Similarity score is a retrieval relevance score, not factual confidence.
- The starter currency tool uses Frankfurter's public endpoint; its supported currencies and availability may change.
- JSON storage is suitable for local demo only. Use a database and authentication before production deployment.

## Deploying on Vercel
Vercel's filesystem is read-only, so chats/FAQs need an external store:
1. Vercel project -> Storage / Marketplace -> add **Upstash Redis** (free) and connect it to the project.
   This adds `KV_REST_API_URL` and `KV_REST_API_TOKEN` automatically.
2. Project -> Settings -> Environment Variables: add `GEMINI_API_KEY`, `WEATHER_API_KEY` (optional).
3. Redeploy.
