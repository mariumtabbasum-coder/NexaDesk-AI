from services.gemini_service import GeminiService
class ResponseService:
    def __init__(self, gemini): self.gemini=gemini
    def answer_from_faq(self,question,results,history):
        context="\n\n".join([f"FAQ {r['faq_id']} ({r['category']}): {r['question']}\nAnswer: {r['answer']}" for r in results])
        prior="\n".join([f"{m['role']}: {m['content']}" for m in history])
        prompt=f"""You are NexaDesk AI, a helpful knowledge assistant. Answer the user's question using ONLY the FAQ context below. Do not invent business policies. If context is insufficient, say so. Be concise, professional and friendly. Conversation context:\n{prior}\nFAQ CONTEXT:\n{context}\nUSER QUESTION:\n{question}"""
        return self.gemini.generate(prompt)
    def unknown_answer(self,question,results):
        suggestions="\n".join([f"- {r['question']}" for r in results if r["similarity"]>0.15])
        return "I couldn't find a reliable answer in the current knowledge base. You can rephrase your question or contact support." + (("\n\n**You might also ask:**\n"+suggestions) if suggestions else "")
    def general_answer(self,question,history):
        prior="\n".join([f"{m['role']}: {m['content']}" for m in history])
        return self.gemini.generate(f"You are NexaDesk AI, a concise helpful assistant. Conversation:\n{prior}\nUser: {question}")
