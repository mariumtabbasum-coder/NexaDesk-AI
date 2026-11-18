import math, re
from services.embedding_service import EmbeddingService
class SemanticSearch:
    def __init__(self, embedding_service): self.embeddings=embedding_service
    @staticmethod
    def cosine(a,b):
        if isinstance(a,dict) and isinstance(b,dict):
            av, bv = a.get("values",[]), b.get("values",[])
            at, bt = a.get("tokens",[]), b.get("tokens",[])
            if not av or not bv: return 0.0
            common=set(at)&set(bt)
            amap=dict(zip(at,av)); bmap=dict(zip(bt,bv))
            dot=sum(amap[t]*bmap[t] for t in common)
            na=math.sqrt(sum(x*x for x in av)); nb=math.sqrt(sum(x*x for x in bv))
        else:
            av,bv=a,b
            dot=sum(x*y for x,y in zip(av,bv))
            na=math.sqrt(sum(x*x for x in av)); nb=math.sqrt(sum(x*x for x in bv))
        return dot/(na*nb) if na and nb else 0.0
    def search(self, query, faqs, top_k=3):
        records=self.embeddings.get_records()
        if len(records)!=len(faqs): records=self.embeddings.rebuild_all(faqs) and self.embeddings.get_records()
        query_vec=self.embeddings.embed(query)
        faq_by_id={f["id"]:f for f in faqs}
        results=[]
        for record in records:
            faq=faq_by_id.get(record["faq_id"])
            if faq:
                score=self.cosine(query_vec, record["embedding"])
                # Local fallback supplements sparse token overlap with shared words.
                if isinstance(query_vec,dict) and isinstance(record["embedding"],dict):
                    q=set(query_vec["tokens"]); d=set(record["embedding"]["tokens"])
                    score=max(score, len(q&d)/max(1,len(q|d)))
                results.append({"faq_id":faq["id"],"question":faq["question"],"answer":faq["answer"],"category":faq.get("category","General"),"similarity":round(float(score),4)})
        return sorted(results,key=lambda r:r["similarity"],reverse=True)[:top_k]
