from utils.storage import JsonStore
class FAQService:
    def __init__(self): self.store=JsonStore("data/faqs.json",[])
    def get_all(self): return self.store.read()
    def add(self,data):
        question=(data.get("question") or "").strip(); answer=(data.get("answer") or "").strip()
        if not question or not answer: raise ValueError("Question and answer are required.")
        items=self.get_all(); new_id=max([x.get("id",0) for x in items] or [0])+1
        item={"id":new_id,"category":(data.get("category") or "General").strip(),"question":question,"answer":answer,"variations":data.get("variations",[]),"keywords":data.get("keywords",[])}
        items.append(item); self.store.write(items); return item
    def update(self,faq_id,data):
        items=self.get_all()
        for i,item in enumerate(items):
            if item["id"]==faq_id:
                item.update({k:data[k] for k in ["question","answer","category","variations","keywords"] if k in data})
                if not item.get("question","").strip() or not item.get("answer","").strip(): raise ValueError("Question and answer are required.")
                self.store.write(items); return item
        return None
    def delete(self,faq_id):
        items=self.get_all(); filtered=[x for x in items if x["id"]!=faq_id]
        if len(filtered)==len(items): return False
        self.store.write(filtered); return True
    def import_items(self,data):
        items=self.get_all(); added=0
        for row in data:
            if row.get("question") and row.get("answer"):
                items.append({"id":max([x.get("id",0) for x in items] or [0])+1,"category":row.get("category","General"),"question":row["question"],"answer":row["answer"],"variations":row.get("variations",[]),"keywords":row.get("keywords",[])})
                added+=1
        self.store.write(items); return added
