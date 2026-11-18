from flask import Flask, render_template, request, jsonify, send_file
from config import Config
from services.faq_service import FAQService
from services.semantic_search import SemanticSearch
from services.embedding_service import EmbeddingService
from services.ai_router import AIRouter
from services.gemini_service import GeminiService
from services.response_service import ResponseService
from utils.storage import JsonStore
from tools.calculator import calculate
from tools.weather import get_weather
from tools.currency import convert_currency
from tools.age_calculator import calculate_age
import os, uuid, datetime, json, io

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.config.from_object(Config)
faq_service = FAQService()
embedding_service = EmbeddingService()
search_service = SemanticSearch(embedding_service)
gemini = GeminiService()
router = AIRouter(gemini)
response_service = ResponseService(gemini)
chat_store = JsonStore("data/chat_history.json", [])
unanswered_store = JsonStore("data/unanswered_questions.json", [])

@app.errorhandler(Exception)
def handle_error(e):
    from werkzeug.exceptions import HTTPException
    if request.path.startswith("/api/"):
        code = e.code if isinstance(e, HTTPException) else 500
        return jsonify({"error": (e.description if isinstance(e, HTTPException) else f"Server error: {e}")}), code
    if isinstance(e, HTTPException):
        return e
    raise e

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "gemini_configured": bool(Config.GEMINI_API_KEY), "weather_configured": bool(Config.WEATHER_API_KEY)})

@app.get("/api/stats")
def stats():
    faqs = faq_service.get_all()
    chats = chat_store.read()
    unanswered = unanswered_store.read()
    cats = sorted(set(f.get("category", "General") for f in faqs))
    return jsonify({"faq_count": len(faqs), "categories": len(cats), "chats": len(chats), "unanswered": len(unanswered), "recent_chats": sorted(chats, key=lambda c:c.get("updated_at",""), reverse=True)[:5]})

@app.route("/api/faqs", methods=["GET", "POST"])
def faqs():
    if request.method == "GET":
        return jsonify(faq_service.get_all())
    data = request.get_json(force=True)
    try:
        item = faq_service.add(data)
        embedding_service.rebuild_all(faq_service.get_all())
        return jsonify(item), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/faqs/<int:faq_id>", methods=["PUT", "DELETE"])
def faq_item(faq_id):
    if request.method == "DELETE":
        deleted = faq_service.delete(faq_id)
        if deleted:
            embedding_service.rebuild_all(faq_service.get_all())
        return jsonify({"success": deleted}), (200 if deleted else 404)
    data = request.get_json(force=True)
    try:
        updated = faq_service.update(faq_id, data)
        if updated:
            embedding_service.rebuild_all(faq_service.get_all())
            return jsonify(updated)
        return jsonify({"error":"FAQ not found"}), 404
    except ValueError as e:
        return jsonify({"error":str(e)}), 400

@app.post("/api/search")
def search():
    payload = request.get_json(force=True)
    query = payload.get("query", "").strip()
    if not query:
        return jsonify({"error":"Enter a search query"}), 400
    results = search_service.search(query, faq_service.get_all(), top_k=3)
    return jsonify({"query":query, "results":results, "embedding_mode": "gemini" if Config.GEMINI_API_KEY else "local fallback"})

@app.post("/api/rebuild-embeddings")
def rebuild_embeddings():
    result = embedding_service.rebuild_all(faq_service.get_all())
    return jsonify(result)

@app.post("/api/import-faqs")
def import_faqs():
    if "file" in request.files:
        try:
            data = json.load(request.files["file"])
        except Exception:
            return jsonify({"error":"Invalid JSON file"}), 400
    else:
        data = request.get_json(force=True)
    if isinstance(data, dict) and "faqs" in data:
        data = data["faqs"]
    if not isinstance(data, list):
        return jsonify({"error":"Import expects a JSON array of FAQ objects"}), 400
    count = faq_service.import_items(data)
    embedding_service.rebuild_all(faq_service.get_all())
    return jsonify({"imported":count, "total":len(faq_service.get_all())})

@app.get("/api/export-faqs")
def export_faqs():
    content = json.dumps(faq_service.get_all(), indent=2, ensure_ascii=False)
    return send_file(io.BytesIO(content.encode("utf-8")), mimetype="application/json", as_attachment=True, download_name="nexadesk_faqs.json")

@app.get("/api/history")
def history():
    items = chat_store.read()
    return jsonify(sorted(items, key=lambda c:c.get("updated_at",""), reverse=True))

@app.post("/api/new-chat")
def new_chat():
    chat = {"id":str(uuid.uuid4()), "title":"New conversation", "messages":[], "created_at":now(), "updated_at":now()}
    items = chat_store.read()
    items.append(chat)
    chat_store.write(items)
    return jsonify(chat)

@app.route("/api/history/<chat_id>", methods=["GET", "DELETE", "PATCH"])
def history_item(chat_id):
    items = chat_store.read()
    chat = next((c for c in items if c["id"] == chat_id), None)
    if not chat:
        return jsonify({"error":"Conversation not found"}), 404
    if request.method == "GET":
        return jsonify(chat)
    if request.method == "DELETE":
        chat_store.write([c for c in items if c["id"] != chat_id])
        return jsonify({"success":True})
    data = request.get_json(force=True)
    chat["title"] = data.get("title", chat["title"])[:80]
    chat["updated_at"] = now()
    chat_store.write(items)
    return jsonify(chat)

@app.post("/api/chat")
def chat():
    payload = request.get_json(force=True)
    message = (payload.get("message") or "").strip()
    chat_id = payload.get("chat_id")
    if not message:
        return jsonify({"error":"Message is required"}), 400
    items = chat_store.read()
    chat_obj = next((c for c in items if c["id"] == chat_id), None)
    if not chat_obj:
        chat_obj = {"id":str(uuid.uuid4()), "title":message[:48], "messages":[], "created_at":now(), "updated_at":now()}
        items.append(chat_obj)
    mode = router.route(message)
    sources = []
    tool_result = None
    answer = ""
    if mode == "calculator":
        tool_result = calculate(message)
        answer = f"**Calculation result:** {tool_result}" if tool_result is not None else "I couldn't safely evaluate that calculation. Try a simple expression such as `450 * 25`."
    elif mode == "weather":
        city = router.extract_city(message)
        tool_result = get_weather(city, Config.WEATHER_API_KEY)
        answer = tool_result.get("message") or f"Weather information for {city}: {tool_result}"
    elif mode == "currency":
        amount, base, target = router.extract_currency(message)
        tool_result = convert_currency(amount, base, target)
        answer = tool_result.get("message", "I couldn't complete that conversion.")
    elif mode == "age":
        birth = router.extract_birth_date(message)
        tool_result = calculate_age(birth) if birth else None
        answer = tool_result.get("message", "Please provide your birth date in YYYY-MM-DD format.")
    elif mode == "knowledge":
        results = search_service.search(message, faq_service.get_all(), top_k=3)
        good = [r for r in results if r["similarity"] >= Config.SIMILARITY_THRESHOLD]
        if good:
            sources = good
            answer = response_service.answer_from_faq(message, good, chat_obj["messages"][-6:])
            mode = "knowledge_search"
        else:
            answer = response_service.unknown_answer(message, results)
            unanswered = unanswered_store.read()
            unanswered.append({"id":str(uuid.uuid4()), "question":message, "created_at":now(), "suggestions":results[:2]})
            unanswered_store.write(unanswered)
            mode = "unknown"
    else:
        answer = response_service.general_answer(message, chat_obj["messages"][-6:])
        mode = "general_ai"
    chat_obj["messages"].append({"role":"user", "content":message, "timestamp":now()})
    chat_obj["messages"].append({"role":"assistant", "content":answer, "timestamp":now(), "mode":mode, "sources":sources, "tool_result":tool_result})
    chat_obj["updated_at"] = now()
    if len(chat_obj["messages"]) == 2:
        chat_obj["title"] = message[:48] + ("…" if len(message)>48 else "")
    chat_store.write(items)
    return jsonify({"chat_id":chat_obj["id"], "answer":answer, "mode":mode, "sources":sources, "tool_result":tool_result})

@app.get("/api/unanswered")
def unanswered():
    return jsonify(unanswered_store.read())

@app.post("/api/feedback")
def feedback():
    payload = request.get_json(force=True)
    chat_id, message_index, rating = payload.get("chat_id"), payload.get("message_index"), payload.get("rating")
    items = chat_store.read()
    chat = next((c for c in items if c["id"] == chat_id), None)
    if chat and isinstance(message_index, int) and 0 <= message_index < len(chat["messages"]):
        chat["messages"][message_index]["feedback"] = rating
        chat_store.write(items)
        return jsonify({"success":True})
    return jsonify({"error":"Message not found"}), 404

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
