import re
class AIRouter:
    def __init__(self, gemini): self.gemini=gemini
    def route(self, text):
        s=text.lower()
        if re.search(r"\b(weather|temperature|forecast|rain|wind)\b",s): return "weather"
        if re.search(r"\b(convert|conversion|exchange rate)\b",s) and re.search(r"\b(usd|eur|gbp|pkr|inr|aed|cad|aud|jpy)\b",s): return "currency"
        if re.search(r"\b(age|how old)\b",s) and re.search(r"\b(19|20)\d\d-\d\d-\d\d\b",s): return "age"
        if re.search(r"\b(calculate|what is|how much is)\b",s) and re.search(r"[\d][\d\s.,]*[+\-*/%^×÷]",s): return "calculator"
        # Tool-like requests are routed explicitly; FAQ knowledge queries get retrieval.
        if re.search(r"\b(reset|refund|payment|price|pricing|account|support|contact|hours|business|product|service|policy|faq|how do i|where can i|what are your|forgot password|cannot access|can\'t access|cant access|unable to login|unable to log in|money back|return my|getting started|how to start)\b",s): return "knowledge"
        return "general"
    def extract_city(self,text):
        m=re.search(r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z .'-]+?)(?:\?|$)",text)
        return re.sub(r"\b(today|tomorrow|right now|currently)\b", "", m.group(1)).strip() if m else "Karachi"
    def extract_currency(self,text):
        amount_match=re.search(r"(\d+(?:\.\d+)?)",text)
        codes=re.findall(r"\b(USD|EUR|GBP|PKR|INR|AED|CAD|AUD|JPY)\b",text.upper())
        amount=float(amount_match.group(1)) if amount_match else 1.0
        base,target=(codes[0],codes[1]) if len(codes)>=2 else ("USD","PKR")
        return amount,base,target
    def extract_birth_date(self,text):
        m=re.search(r"\b(19|20)\d\d-\d\d-\d\d\b",text); return m.group(0) if m else None
