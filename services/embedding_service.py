import json, os, re, math
from config import Config
from google import genai
from utils.storage import JsonStore
class EmbeddingService:
    def __init__(self):
        self.store = JsonStore("data/faq_embeddings.json", [])
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None
    def embed(self, text):
        if self.client:
            try:
                res = self.client.models.embed_content(model=Config.GEMINI_EMBED_MODEL, contents=text)
                return res.embeddings[0].values
            except Exception:
                pass
        # Lightweight local fallback: token count vector over normalized tokens.
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        vocab = sorted(set(tokens))
        vector = [tokens.count(t) for t in vocab]
        return {"tokens":vocab, "values":vector}
    def rebuild_all(self, faqs):
        records=[]
        for faq in faqs:
            texts=[faq.get("question","")] + faq.get("variations",[])
            combined=" ".join(texts + faq.get("keywords",[]))
            records.append({"faq_id":faq["id"], "text":combined, "embedding":self.embed(combined)})
        self.store.write(records)
        return {"success":True, "count":len(records), "mode":"gemini" if self.client else "local fallback"}
    def get_records(self):
        return self.store.read()
